# BOOTSTRAP-264 — AXIOM WASM BACKEND + TARGET CLASSIFICATION

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này là chứng minh `Axiom LIR` không chỉ độc lập với nhiều ISA kiểu register machine, mà còn độc lập với **stack-based virtual machine** như WebAssembly.

Đây cũng là bước hoàn thiện kiến trúc target classification:

```text
                    Axiom LIR
                        │
             TargetBackend Contract
                        │
       ┌────────────────┼─────────────────┐
       │                │                 │
     Native            Native             VM
   Register ISA      Register ISA      Stack ISA
       │                │                 │
    x86-64             ARM64             WASM
    RV64               ...               ...
```

---

# 1. WASM không phải CPU giả lập

Axiom không được coi WASM là:

```text
"CPU target đặc biệt"
```

mà là:

> **portable virtual machine target với module/linking/runtime contract riêng.**

Điều này rất quan trọng vì WASM không có register file vật lý theo cách x86/ARM/RISC-V có.

---

# 2. Target families

`TargetSpec` nên có:

```text
TargetFamily {
    Native
    VirtualMachine
    Accelerator
}
```

Ví dụ:

```text
x86_64 → Native
aarch64 → Native
riscv64 → Native
wasm32 → VirtualMachine
wasm64 → VirtualMachine
gpu → Accelerator
```

Nhưng đây chỉ là compiler metadata, không phải semantic distinction trong Core.

---

# 3. WASM targets

V1:

```text
wasm32
wasm64
```

Trong đó:

```text
wasm32 → i32 address model
wasm64 → i64 address model
```

---

# 4. Core pointer semantics không thay đổi

Axiom:

```text
Place
Pointer
Address
Integer
Provenance
```

vẫn là các khái niệm khác nhau.

WASM:

```text
linear-memory offset
```

không tự động trở thành Axiom pointer provenance.

---

# 5. Linear memory

WASM có:

```text
Memory
```

với:

```text
pages
```

thường mỗi page là:

```text
64 KiB
```

Compiler phải coi linear memory là một **storage domain**.

---

# 6. Storage domain

Thêm target domain:

```text
LinearMemory
```

nhưng không cần thêm kiểu Core mới.

---

# 7. Axiom allocation

`Box<T>` / `Vec<T>` / allocator library có thể được lower vào WASM linear memory.

Nhưng:

```text
Box<T>
```

không có nghĩa:

```text
WASM linear memory object
```

ở semantic level.

---

# 8. Address representation

WASM32:

```text
address → i32
```

WASM64:

```text
address → i64
```

nhưng compiler nội bộ vẫn giữ:

```text
AddressValue
```

riêng biệt trước target lowering.

---

# 9. Không được làm

Không được thiết kế LIR kiểu:

```text
Address = i32
```

vì sẽ làm LIR phụ thuộc WASM32.

---

# 10. LIR address

Nên là:

```text
Address {
    base
    offset
    address_space
    alignment
}
```

Sau đó WASM lowering mới quyết định representation.

---

# 11. WASM operand stack

WASM instruction có mô hình:

```text
operand stack
```

Ví dụ conceptual:

```text
local.get 0
local.get 1
i32.add
```

---

# 12. Nhưng Axiom LIR vẫn SSA-like

Không biến LIR thành stack machine.

Ví dụ:

```text
v3 = add v1, v2
```

sau WASM lowering:

```text
local.get v1
local.get v2
i32.add
local.set v3
```

---

# 13. Tại sao không dùng stack IR ngay từ đầu?

Vì nếu dùng:

```text
push
push
add
pop
```

thì:

- khó SSA analysis
- khó MemorySSA
- khó register backend
- khó debug
- khó common optimization

Axiom giữ SSA-like representation đến cuối.

---

# 14. WASM locals

WASM backend tạo:

```text
LocalId → WASM local
```

---

# 15. Local allocation

Có thể merge nhiều virtual values vào cùng WASM local nếu lifetime không overlap.

Đây tương tự register allocation nhưng đơn giản hơn.

---

# 16. Operand stack scheduling

Backend có thể tránh `local.set/get` không cần thiết bằng cách giữ temporary trên operand stack.

Ví dụ:

```text
v3 = add(v1, v2)
v4 = mul(v3, 2)
```

có thể:

```text
local.get v1
local.get v2
i32.add
i32.const 2
i32.mul
local.set v4
```

---

# 17. Stackification

Đây là pass riêng:

```text
WASM Stackification
```

Input:

```text
SSA / Machine-like IR
```

Output:

```text
WASM stack-compatible IR
```

---

# 18. Stackification không thay đổi semantics

Nó chỉ thay đổi representation.

---

# 19. Structured control flow

Đây là khác biệt lớn.

Axiom MIR có thể có CFG:

```text
A → B
A → C
B → D
C → D
```

WASM yêu cầu structured control flow.

---

# 20. WASM blocks

Backend dùng:

```text
block
loop
if
else
br
br_if
br_table
```

---

# 21. Arbitrary CFG

Không được giả định:

```text
Axiom CFG = WASM CFG
```

---

# 22. CFG structuring

Cần pass:

```text
CFG → StructuredControlFlow
```

---

# 23. Irreducible CFG

Nếu CFG không biểu diễn trực tiếp được bằng structured constructs, backend phải:

```text
restructure
```

hoặc sử dụng dispatcher/state-machine technique.

---

# 24. Không thay đổi Core

Axiom Core vẫn không có:

```text
goto
```

Safe Core.

MIR vẫn có CFG đầy đủ.

---

# 25. Loop

Axiom:

```text
loop {
    ...
}
```

có thể lower trực tiếp thành WASM:

```text
loop
    ...
    br_if
end
```

---

# 26. `if`

Axiom:

```text
if condition {
    A
} else {
    B
}
```

có thể:

```text
if
   A
else
   B
end
```

---

# 27. Return

WASM:

```text
return
```

---

# 28. Panic/trap

Axiom panic semantics được map theo runtime/profile.

Có thể:

```text
unreachable
```

nếu profile là abort/trap.

Nếu cần panic runtime:

```text
call axiom_panic
```

---

# 29. Runtime không bắt buộc

WASM program nhỏ chỉ dùng:

```text
startup
memory
```

hoặc thậm chí host-provided imports.

Không được tự động kéo toàn bộ Axiom runtime.

---

# 30. WASM function calls

WASM có:

```text
call
call_indirect
```

---

# 31. Static dispatch

Axiom generic/static calls:

```text
call
```

nếu target known.

---

# 32. Dynamic dispatch

`dyn Trait` có thể lower thành:

```text
table + context
```

hoặc representation ABI khác.

Không được coi `call_indirect` là bắt buộc cho mọi callable.

---

# 33. Function pointers

WASM function references/table semantics là backend representation.

Axiom function pointer remains semantic callable value.

---

# 34. Tables

WASM table:

```text
Table
```

là một resource/module-level construct.

Không phải universal Axiom object table.

---

# 35. Indirect calls

Backend cần validate:

```text
signature
table index
function type
```

---

# 36. Type safety

`call_indirect` signature mismatch phải trap theo WASM semantics.

Axiom compiler phải đảm bảo generated call site đúng signature.

---

# 37. Closures

Axiom capturing closure:

```text
code + environment
```

có thể lower thành:

```text
function index
environment pointer/index
```

---

# 38. Closure environment

Environment không cần WASM object header.

---

# 39. Escape analysis

Nếu closure không escape:

```text
environment allocation
```

có thể biến mất.

---

# 40. Non-capturing closure

Có thể lower trực tiếp thành function reference.

---

# 41. Async

WASM backend không được giả định native OS threads.

Axiom async vẫn là:

```text
Future state machine
```

---

# 42. WASM async

Có thể chạy bằng:

```text
host executor
```

hoặc Axiom runtime.

Không phải Core requirement.

---

# 43. WASI

WASI thuộc:

```text
Platform/System profile
```

không thuộc WASM Core.

---

# 44. Browser

Browser environment cũng là target environment riêng:

```text
wasm32-browser
```

---

# 45. WASI

Ví dụ:

```text
wasm32-wasi
```

có:

```text
filesystem
stdin/stdout
clock
random
network
```

tùy capability.

---

# 46. Không có hidden OS authority

Một WASM binary không tự nhiên có quyền filesystem/network.

---

# 47. Imports

Host capability được biểu diễn bằng:

```text
imports
```

---

# 48. Axiom effect system

Foreign WASM import phải khai báo effect:

```text
IO
External
Synchronize
```

nếu phù hợp.

---

# 49. Host function

Ví dụ conceptual:

```text
extern "wasm" fn host_log(...)
```

nhưng API cụ thể nằm ở platform/FFI layer.

---

# 50. Memory import

WASM memory có thể:

```text
defined internally
```

hoặc:

```text
imported from host
```

---

# 51. Ownership

Imported memory không tự động trở thành Axiom-owned storage.

Phải có FFI/storage contract.

---

# 52. Shared memory

WASM threads + shared memory yêu cầu:

```text
shared memory
atomics
```

---

# 53. Atomic support

Backend chỉ bật atomic operations nếu target supports threads/shared memory.

---

# 54. Memory ordering

Axiom:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

phải được lower thành WASM atomic semantics tương ứng.

---

# 55. Không được map atomic thành ordinary load/store

---

# 56. `memory.atomic.wait`

WASM có wait/notify primitives cho shared memory.

Đây có thể là backend primitive cho:

```text
parking
```

nhưng synchronization abstraction vẫn thuộc library/runtime.

---

# 57. SIMD

WASM SIMD sử dụng vector width cố định theo WASM SIMD model.

Axiom vector semantics vẫn độc lập.

---

# 58. SIMD lowering

```text
VectorOp<T,N>
       ↓
WASM SIMD
```

nếu operation được target hỗ trợ.

---

# 59. Scalable vector

WASM V1 không phải scalable vector model như RISC-V V.

Do đó:

```text
ScalableVector
```

phải legalize/reject tùy target.

---

# 60. Numeric types

WASM native numeric primitives:

```text
i32
i64
f32
f64
```

---

# 61. Axiom smaller integer types

Ví dụ:

```text
i8
i16
u8
u16
```

có thể được registerized bằng:

```text
i32
```

nhưng semantic type vẫn là i8/i16.

---

# 62. Sign extension

Backend phải insert:

```text
extend
truncate
```

khi cần.

---

# 63. Integer overflow

Axiom numeric semantics quyết định.

WASM wrapping operations chỉ được sử dụng nếu semantics tương ứng.

---

# 64. Checked arithmetic

Có thể generate:

```text
compare
branch
trap/result
```

tùy Axiom operation.

---

# 65. Division

WASM có semantics riêng cho signed/unsigned division.

Backend phải preserve Axiom division semantics, đặc biệt:

```text
division by zero
signed overflow
```

---

# 66. Floating point

WASM FP semantics phải được kiểm tra với Axiom strict FP contract.

Không tự động áp dụng fast-math.

---

# 67. NaN

Compiler không được canonicalize NaN nếu làm thay đổi observable Axiom semantics.

---

# 68. Memory alignment

WASM instructions có alignment hint.

Hint không tự động thay đổi semantic alignment requirement của Axiom.

---

# 69. Unaligned

Nếu Axiom operation cho phép unaligned access:

```text
WASM load/store
```

phải được emit với semantics phù hợp.

---

# 70. Bounds

Linear memory access có runtime bounds check/trap semantics.

Axiom bounds semantics vẫn là authority.

---

# 71. Bounds-check elimination

Nếu compiler đã chứng minh:

```text
index < length
```

và linear-memory mapping an toàn, check có thể được loại bỏ.

---

# 72. Không được loại bỏ check chỉ vì WASM thường trap.

---

# 73. Pointer provenance

Đây là điểm đặc biệt quan trọng.

WASM có:

```text
numeric memory index
```

nhưng Axiom có:

```text
provenance
```

---

# 74. Integer → pointer

Một integer được tạo từ:

```text
i32
```

không tự động trở thành:

```text
*mut T
```

safe Axiom pointer.

---

# 75. Unsafe boundary

Nếu system API cho phép:

```text
raw address → pointer
```

phải đi qua unsafe contract.

---

# 76. `address_of`

Axiom:

```text
address_of(x)
```

vẫn là unsafe/system concept.

---

# 77. WASM address observability

Nếu code exposes linear-memory address ra host:

```text
address becomes observable
```

compiler không được tùy ý relocate storage mà host vẫn giữ địa chỉ cũ.

---

# 78. Nhưng nếu address không escape

Compiler vẫn có thể:

```text
scalarize
stack-promote
eliminate
```

storage.

---

# 79. `Vec`

WASM implementation của `Vec` có thể dùng:

```text
linear memory
```

nhưng semantic relocation rules vẫn giữ nguyên.

---

# 80. `view`

Axiom:

```text
view<T>
```

có thể lower thành:

```text
{pointer, length}
```

trong WASM32.

---

# 81. `mut_view`

Tương tự về representation nhưng compiler vẫn giữ:

```text
exclusive WRITE capability
```

---

# 82. Representation ≠ capability

Hai `view` có thể cùng binary shape nhưng semantic permissions khác nhau.

---

# 83. Global/static

Axiom `static` có thể lower thành:

```text
data segment
```

hoặc:

```text
BSS-equivalent runtime initialization
```

nếu platform hỗ trợ.

---

# 84. TLS

WASM32 không có TLS ABI universal tương đương native OS.

TLS phải thuộc:

```text
runtime/platform implementation
```

---

# 85. Không đưa TLS assumptions vào WASM backend Core.

---

# 86. WASM64

WASM64 thay đổi pointer/index width nhưng không thay đổi Axiom pointer semantics.

---

# 87. Target DataLayout

```text
wasm32:
pointer_width = 32

wasm64:
pointer_width = 64
```

---

# 88. ABI

Axiom-to-WASM ABI phải xác định:

```text
scalar parameters
scalar returns
aggregate parameters
aggregate returns
strings
views
closures
function pointers
```

---

# 89. Scalar ABI

Ví dụ:

```text
i32 → wasm i32
i64 → wasm i64
f32 → wasm f32
f64 → wasm f64
```

---

# 90. Small integer ABI

`u8/i8/u16/i16/bool` có thể ABI-lower thành i32 với extension/truncation semantics.

---

# 91. Struct ABI

Có hai lựa chọn:

```text
multi-value
```

hoặc:

```text
memory representation + pointer
```

Compiler ABI classifier quyết định.

---

# 92. Multi-value

Nếu target supports multi-value, một số aggregates có thể return nhiều scalar values.

---

# 93. Không bắt buộc heap allocation cho aggregate return.

---

# 94. sret

Aggregate lớn có thể lower thành:

```text
caller-provided result area
```

với pointer internal.

---

# 95. Pointer hidden parameter

Đây là ABI lowering detail.

Programmer không thấy nó.

---

# 96. Variadic functions

WASM không có C-style variadic ABI trực tiếp tương đương native.

Axiom:

```text
variadic
```

phải được giới hạn bởi ABI/FFI layer.

---

# 97. Core không cần hứa WASM variadic support.

Có thể:

```text
reject
```

hoặc implement bằng explicit argument array/ABI adapter.

---

# 98. C FFI

`extern "C"` trên WASM phải sử dụng WASM C ABI/profile tương ứng.

---

# 99. `repr(C)`

Vẫn là representation contract, không phải magic pointer semantics.

---

# 100. Object/module model

AxiomObject cho WASM nên hỗ trợ:

```text
WasmObject {
    TypeSection
    ImportSection
    FunctionSection
    TableSection
    MemorySection
    GlobalSection
    ExportSection
    ElementSection
    CodeSection
    DataSection
    CustomSections
}
```

---

# 101. Custom sections

Có thể chứa:

```text
debug
.axmeta
producers
source mapping
build metadata
```

---

# 102. `.axmeta`

Có thể:

```text
embedded
```

hoặc:

```text
external
```

tùy profile.

---

# 103. Debug

WASM có thể dùng DWARF/custom debug metadata.

Axiom source mapping:

```text
SourceSpan
→ MIR
→ WASM instruction offset
```

---

# 104. Name section

Có thể emit function/local names trong debug profile.

---

# 105. Release profile

Có thể strip:

```text
debug names
debug sections
unneeded metadata
```

---

# 106. Dead stripping

WASM linker có thể loại bỏ:

```text
unused functions
unused data
unused runtime components
```

nếu không observable.

---

# 107. Exports là roots

Nếu:

```text
@export fn foo()
```

thì `foo` là linker root.

---

# 108. Imports là dependencies

Imported functions/tables/memory được xem là external effects/resources.

---

# 109. Component Model

Axiom không được gắn chặt vào WASM Component Model trong Core.

Nó là:

```text
WASM platform/application ABI layer
```

---

# 110. WIT

Nếu hỗ trợ Component Model:

```text
Axiom type
 ↓
WIT adapter
 ↓
component ABI
```

---

# 111. Không thay đổi semantic type system.

---

# 112. Strings trong WASM ABI

Axiom:

```text
String
Str
Bytes
```

không thể tự động coi là cùng một ABI type.

---

# 113. FFI string

Có thể dùng explicit ABI descriptor:

```text
(ptr, len)
```

hoặc:

```text
ptr to NUL
```

tùy contract.

---

# 114. UTF-8 validity

`Str` phải giữ invariant UTF-8.

Host-provided bytes không tự động trở thành `Str`.

---

# 115. Handle ABI

Logical handles có thể được truyền như:

```text
i32/i64
```

nhưng không biến thành raw pointer.

---

# 116. Resource handles

WASI/Component Model resource handles thuộc platform contract.

---

# 117. Security

WASM sandbox không thay thế Axiom safety.

Có hai tầng:

```text
Axiom semantic safety
WASM host capability sandbox
```

---

# 118. Một chương trình có thể:

```text
unsafe Axiom
```

nhưng vẫn chạy trong sandbox WASM.

Ngược lại, safe Axiom không đồng nghĩa host cấp quyền filesystem/network.

---

# 119. GPU/WebGPU

WASM có thể gọi WebGPU hoặc host GPU API.

Đó là FFI/platform capability.

Không đưa WebGPU objects vào WASM Core.

---

# 120. WASM threads

Execution domain:

```text
Thread
```

vẫn dùng Axiom concurrency semantics.

---

# 121. Shared memory

Nếu target hỗ trợ:

```text
SharedMemory
```

phải explicit.

---

# 122. Atomics

Axiom Atomic semantics map xuống WASM atomic instructions khi có feature.

---

# 123. `Send`

WASM worker/thread environment quyết định execution domain.

Axiom `Send` vẫn là semantic property.

---

# 124. `Share`

Không tự động phát sinh chỉ vì WASM memory có thể shared.

---

# 125. Async + WASM

Browser async thường dựa trên host event loop.

Axiom:

```text
Future
```

vẫn không đồng nghĩa:

```text
JavaScript Promise
```

---

# 126. JS interop

Nếu cần:

```text
Axiom Future
↔ JS Promise
```

phải có explicit adapter.

---

# 127. Exception handling

WASM exception handling feature có thể được target support.

Nhưng Axiom v1 không có exception semantics.

Do đó không được đưa exception vào Core chỉ vì WASM hỗ trợ nó.

---

# 128. Panic

Axiom panic vẫn có semantics riêng.

WASM exception mechanism chỉ là một implementation option nếu profile cho phép.

---

# 129. GC proposal

Axiom không phụ thuộc WASM GC.

Đặc biệt:

```text
Axiom no mandatory GC
```

vẫn giữ nguyên.

---

# 130. Reference types

WASM `externref`, `funcref`... có thể được sử dụng trong FFI/runtime layer.

Không trở thành universal Axiom reference type.

---

# 131. Host references

Một host reference phải được biểu diễn như:

```text
opaque external handle
```

nếu cần.

---

# 132. Memory64

WASM64 hỗ trợ address space lớn hơn nhưng Axiom semantic storage vẫn độc lập.

---

# 133. `memory.grow`

Grow có thể invalidate physical addresses/host views tùy embedding/runtime contract.

Do đó compiler phải coi memory relocation/invalidation là semantic fact khi applicable.

---

# 134. Active Axiom `view`

Nếu `view` trỏ vào storage có thể relocate khi grow:

```text
grow
```

phải bị chặn khi live capability yêu cầu stability, hoặc API phải establish stable storage.

---

# 135. Đây chính là invariant từ memory model được kiểm chứng trên WASM.

---

# 136. WASM code generation pipeline

```text
Verified MIR
    ↓
Semantic OptIR
    ↓
ABI MIR
    ↓
Axiom LIR
    ↓
WASM Legalization
    ↓
WASM SSA-like IR
    ↓
CFG Structuring
    ↓
Stackification
    ↓
Local Allocation
    ↓
WASM Instruction Selection
    ↓
WASM Validation
    ↓
Binary Encoder
    ↓
.wasm
```

---

# 137. Không cần:

```text
register allocation
```

theo nghĩa native CPU.

---

# 138. Nhưng vẫn có:

```text
local allocation
stack scheduling
```

để giảm code size và local traffic.

---

# 139. WASM validator

Phải validate:

```text
stack typing
block signatures
branch depths
locals
globals
memory indexes
table indexes
function types
feature usage
```

---

# 140. Compiler không nên dựa vào external validator để phát hiện lỗi nội bộ.

Axiom phải có:

```text
WasmMachineVerifier
```

trước encoder/output.

---

# 141. Binary encoder

Sau verification mới emit:

```text
magic
version
sections
instructions
data
custom sections
```

---

# 142. Canonical encoding

Encoder phải deterministic.

Cùng:

```text
Axiom source
compiler semantic version
target
features
profile
dependencies
```

→ cùng binary trong reproducible mode.

---

# 143. WASM feature set

Ví dụ:

```text
WasmFeatures {
    multi_value
    bulk_memory
    reference_types
    simd
    threads
    exceptions
    memory64
    tail_call
    ...
}
```

---

# 144. Feature dependency

Ví dụ:

```text
threads
→ shared-memory support
→ atomics
```

Compiler phải validate feature closure.

---

# 145. Unsupported feature

Nếu source/library yêu cầu feature không có:

```text
compile-time diagnostic
```

Không fallback sai semantics.

---

# 146. Portable WASM profile

Có thể định nghĩa:

```text
wasm-portable
```

chỉ dùng feature baseline.

---

# 147. Optimized WASM profile

Ví dụ:

```text
wasm32-simd
wasm32-threads
wasm64
```

---

# 148. Browser profile

Có thể:

```text
wasm32-browser
```

với platform imports.

---

# 149. WASI profile

```text
wasm32-wasi
```

---

# 150. Embedded WASM

Có thể nhúng `.wasm` vào host application mà không cần WASI.

---

# 151. Target classification sau 264

Axiom giờ có:

```text
Target
├── Native
│   ├── RegisterISA
│   │   ├── x86-64
│   │   ├── ARM64
│   │   └── RV64
│
├── VirtualMachine
│   ├── WASM32
│   └── WASM64
│
└── Accelerator
    └── GPU
```

---

# 152. Nhưng frontend chỉ thấy:

```text
TargetSpec
```

Không có:

```text
if wasm
if x86
if arm
```

trong semantic Core.

---

# 153. Compiler architecture hoàn chỉnh hơn

```text
                 Source
                   │
                   ▼
               Semantic
                   │
                   ▼
             Verified MIR
                   │
                   ▼
                OptIR
                   │
                   ▼
               ABI MIR
                   │
                   ▼
               Axiom LIR
                   │
          TargetBackend Contract
                   │
       ┌───────────┼────────────┐
       │           │            │
       ▼           ▼            ▼
    Native      Native          VM
     x86         ARM           WASM
     RV64                       32/64
       │           │            │
       ▼           ▼            ▼
  Machine IR   Machine IR   WASM IR
       │           │            │
       └───────────┼────────────┘
                   ▼
              AxiomObject
```

---

# 154. Những gì 264 đã chứng minh

### 1. Không phụ thuộc FLAGS

x86 có FLAGS, ARM có condition flags, RISC-V khác mô hình.

Axiom LIR vẫn hoạt động.

### 2. Không phụ thuộc fixed register set

RISC-V V đã phá giả định vector width cố định.

### 3. Không phụ thuộc addressing mode

x86 có complex addressing; ARM/RISC-V khác; WASM thậm chí không có register addressing tương tự.

### 4. Không phụ thuộc register machine

WASM không phải native register ISA.

### 5. Không phụ thuộc GC

WASM GC là optional platform feature.

### 6. Không phụ thuộc OS

Browser/WASI/embedded WASM có môi trường khác nhau.

---

# 155. Invariants — `AWASM-20..95`

```text
AWASM-20
WASM is a target family, not a Core semantic model.

AWASM-21
Axiom LIR must remain independent of WASM operand-stack representation.

AWASM-22
WASM stackification occurs only after semantic optimization.

AWASM-23
WASM locals are backend representation.

AWASM-24
Linear-memory offsets are not automatically Axiom pointers.

AWASM-25
Integer-to-pointer conversion does not establish Axiom provenance.

AWASM-26
WASM memory is an explicit storage domain.

AWASM-27
WASM32 and WASM64 differ in physical address width, not Core pointer semantics.

AWASM-28
Axiom ownership and capability rules remain active on WASM.

AWASM-29
view and mut_view preserve their semantic capabilities after lowering.

AWASM-30
WASM memory growth must respect storage invalidation contracts.

AWASM-31
Address observability constrains storage elimination and relocation.

AWASM-32
Bounds-check elimination requires Axiom-level proof.

AWASM-33
WASM traps do not replace Axiom semantic verification.

AWASM-34
Atomic operations must preserve Axiom memory ordering.

AWASM-35
Shared memory does not imply Axiom Share.

AWASM-36
WASM threads do not alter Send semantics.

AWASM-37
WASI is a platform contract, not Core.

AWASM-38
Browser host APIs are explicit FFI/capability boundaries.

AWASM-39
Host imports carry appropriate effect/resource contracts.

AWASM-40
Imported memory is not implicitly Axiom-owned memory.

AWASM-41
Imported resources require explicit lifetime/ownership contracts.

AWASM-42
Function references do not imply Axiom object headers.

AWASM-43
call_indirect is an explicit dynamic dispatch representation.

AWASM-44
Static dispatch must not silently become dynamic dispatch.

AWASM-45
Closure environments need no mandatory heap allocation.

AWASM-46
Async remains a Future state machine on WASM.

AWASM-47
Axiom does not require WASM GC.

AWASM-48
WASM reference types are platform/FFI representations, not universal Core references.

AWASM-49
WASM SIMD does not redefine Axiom vector semantics.

AWASM-50
WASM scalable-vector absence must not contaminate Core.

AWASM-51
Aggregate ABI classification is target-specific.

AWASM-52
sret is an ABI lowering mechanism, not a source-level feature.

AWASM-53
WASM variadic limitations must remain in ABI/FFI layers.

AWASM-54
WASM exception facilities do not introduce Axiom exceptions.

AWASM-55
Panic implementation may use WASM trap/host runtime according to profile.

AWASM-56
WASM module exports are linker roots.

AWASM-57
WASM imports are explicit external dependencies.

AWASM-58
Unused runtime components must not be linked.

AWASM-59
WASM custom metadata must remain removable when not requested.

AWASM-60
WASM output must be deterministic under reproducible build mode.

AWASM-61
WASM feature sets are explicit target facts.

AWASM-62
Unavailable WASM features must cause compile-time rejection or legal fallback.

AWASM-63
WASM validation precedes binary emission.

AWASM-64
The compiler must not rely on external validation to guarantee internal correctness.

AWASM-65
Structured control flow is a backend representation.

AWASM-66
Axiom MIR may retain arbitrary CFG structure.

AWASM-67
CFG structuring must preserve observable semantics.

AWASM-68
Irreducible CFGs require explicit backend legalization.

AWASM-69
Stackification must preserve SSA value semantics.

AWASM-70
Local allocation must preserve value liveness.

AWASM-71
WASM memory ordering remains distinct from host synchronization contracts.

AWASM-72
WASI/host capabilities never appear implicitly.

AWASM-73
Axiom FFI safety rules apply to WASM imports and exports.

AWASM-74
Debug source provenance should survive WASM lowering.

AWASM-75
WASM code generation is semantically equivalent to reference execution.

AWASM-76
WASM target-specific optimization cannot alter Core semantics.

AWASM-77
WASM backend caches include target/features/ABI/profile identity.

AWASM-78
WASM binary stripping must respect exports, reflection and FFI roots.

AWASM-79
Component Model integration is an ABI/platform layer.

AWASM-80
WIT mappings must not redefine Axiom types.

AWASM-81
Host callbacks must preserve resource/lifetime contracts.

AWASM-82
WASM memory addresses exposed externally become observable state.

AWASM-83
Linear-memory numeric identity is distinct from logical identity.

AWASM-84
Handle values remain logical identities, not memory capabilities.

AWASM-85
WASM backend must pass common TargetBackend conformance tests.

AWASM-86
Native and WASM implementations must agree on observable semantics.

AWASM-87
Differences in physical representation are not semantic differences.

AWASM-88
No WASM-specific syntax is required in Core v1.

AWASM-89
Adding WASM features must not require changing ownership semantics.

AWASM-90
Adding WASM features must not require changing trait semantics.

AWASM-91
Adding WASM features must not require changing async semantics.

AWASM-92
Adding WASM features must not require changing numeric semantics.

AWASM-93
Adding WASM features must not require changing FFI safety semantics.

AWASM-94
The WASM backend must remain replaceable without changing frontend semantics.

AWASM-95
WASM is a validation target for the portability of Axiom LIR.
```

---

# 156. Kiến trúc backend hiện tại

Đến đây, backend đã có một boundary rất rõ:

```text
                   ┌─────────────────────┐
                   │     AXIOM CORE      │
                   │                     │
                   │ types               │
                   │ ownership           │
                   │ capabilities        │
                   │ effects             │
                   │ concurrency         │
                   │ async               │
                   │ comptime            │
                   │ FFI semantics       │
                   └──────────┬──────────┘
                              │
                              ▼
                        Verified MIR
                              │
                              ▼
                           OptIR
                              │
                              ▼
                          ABI MIR
                              │
                              ▼
                         AXIOM LIR
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
              x86-64        ARM64        RV64
                 │            │            │
                 └────────────┼────────────┘
                              │
                              ▼
                           Native
                             
                         + WASM32/64
                              │
                              ▼
                         Virtual VM
```

**Đây là boundary mà tôi khuyến nghị giữ cố định.**

Từ đây, thêm target mới như MIPS, PowerPC, LoongArch, SPARC, WebAssembly component target... không được phép kéo ngược kiến trúc vào Core.

---

## Bước tiếp theo: BOOTSTRAP-265

Sau khi đã có x86-64 + ARM64 + RV64 + WASM, task hợp lý tiếp theo không phải thêm CPU thứ năm.

Nên chuyển sang:

### **BOOTSTRAP-265 — AXIOM TARGET INDEPENDENT MACHINE SEMANTICS + BACKEND CONFORMANCE FORMALIZATION**

Mục tiêu là **đóng băng hoàn toàn boundary giữa LIR và backend**, định nghĩa:

```text
LIR Operation
    ↓
Target Legalization Contract
    ↓
Machine Semantics
    ↓
Target Instruction Sequence
    ↓
Machine Verification
```

và quan trọng hơn:

```text
x86-64 executable
ARM64 executable
RV64 executable
WASM executable
       │
       ▼
   Same Axiom
 Observable
  Semantics
```

Task 265 sẽ biến toàn bộ phần backend vừa thiết kế thành **một contract mà agent/compiler developer có thể implement trực tiếp**, thay vì chỉ là kiến trúc mô tả.