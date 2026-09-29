# BOOTSTRAP-779 — AXABI

**Title:** Native Axiom ABI, Calling Convention, Register/Stack Contract, Scalar/Aggregate Representation, Struct/Enum/Union ABI, Return/Parameter Passing, Variadic Boundary, SIMD/Vector ABI, Name Mangling, TLS ABI, Unwind ABI, C ABI Interoperability & Cross-Platform ABI 5.0  
**Namespace:** `AXABI`  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXABI` định nghĩa **machine-level contract** giữa các compilation units, libraries, executables, runtime components và foreign code.

```text
AXCOMPILER
    │
    ▼
┌──────────────┐
│    AXABI     │
│              │
│ calling      │
│ convention   │
│ parameters   │
│ returns      │
│ registers    │
│ stack        │
│ aggregates   │
│ TLS          │
│ unwind       │
│ FFI          │
└──────┬───────┘
       │
       ├──────────────┐
       ▼              ▼
   AXOBJECT       AXRUNTIME
       │
       ▼
   AXLINKER
```

ABI phải đủ chặt để:

- compiler khác version vẫn gọi được binary-compatible code;
- dynamic library hoạt động;
- static library hoạt động;
- Axiom gọi C ABI;
- C/C++ có thể gọi Axiom qua C ABI;
- runtime và compiler không cần biết implementation nội bộ của nhau;
- self-hosted compiler có thể dùng chính ABI của Axiom.

---

# 2. Boundary

### AXABI sở hữu

- calling convention;
- register allocation contract tại call boundary;
- stack argument layout;
- parameter passing;
- return value passing;
- aggregate ABI;
- scalar representation;
- alignment;
- struct/union/enum ABI;
- function pointer ABI;
- closure ABI boundary;
- variadic ABI boundary;
- SIMD/vector ABI;
- TLS ABI;
- unwind ABI contract;
- C ABI mapping;
- symbol naming/mangling contract;
- ABI compatibility/versioning.

### Không sở hữu

```text
AXCOMPILER
→ semantic type system

AXOBJECT
→ object file container

AXLINKER
→ global symbol resolution

AXLOADER
→ runtime image loading

AXSTARTUP
→ process startup

AXRUNTIME
→ runtime services

AXMEMORY
→ allocation/lifetime implementation

AXTASK
→ scheduling

AXCRYPTO
→ cryptography
```

---

# 3. Core principle

Axiom ABI phải ưu tiên:

```text
zero-cost
predictability
native-code compatibility
small runtime
stable binary contract
```

Không được tạo một ABI “cao cấp” khiến compiler phải chèn runtime machinery cho mỗi function call.

---

# 4. ABI layers

```text
                AXABI
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
   Axiom ABI    C ABI    Platform ABI
       │          │          │
       └──────┬───┴──────────┘
              ▼
       Machine ABI
```

---

# 5. ABI profile

```text
AbiProfile {
    architecture
    operating_system
    object_format
    endian
    pointer_width

    calling_convention
    register_set
    stack_rules

    scalar_rules
    aggregate_rules
    return_rules

    tls_rules
    unwind_rules

    symbol_rules
    ffi_rules

    vector_rules
    variadic_rules

    version
}
```

---

# 6. ABI identity

ABI identity phải bao gồm tối thiểu:

```text
architecture
platform
OS ABI
calling convention
pointer model
alignment model
scalar representation
aggregate rules
exception/unwind model
TLS model
```

---

# 7. ABI fingerprint

```text
abi_fingerprint =
    hash(
        canonical ABI descriptor
    )
```

Fingerprint được sử dụng bởi:

- AXOBJECT;
- AXLINKER;
- AXTOOLCHAIN;
- AXBUILD;
- package compatibility;
- dynamic loader.

---

# 8. ABI compatibility classes

```text
EXACT
BACKWARD_COMPATIBLE
FORWARD_COMPATIBLE
SOURCE_COMPATIBLE_ONLY
INCOMPATIBLE
```

---

# 9. Exact ABI

Binary có thể link trực tiếp nếu:

```text
ABI fingerprint == expected fingerprint
```

---

# 10. Compatibility rule

Không được coi hai ABI tương thích chỉ vì:

```text
same architecture
```

Ví dụ:

```text
x86_64 Windows
```

không đủ để xác định ABI.

---

# 11. Baseline architectures

Axiom 5.0:

```text
x86_64
AArch64
WASM32
```

Kiến trúc mới phải cung cấp ABI backend riêng.

---

# 12. Endianness

Baseline native targets:

```text
x86_64  → little-endian
AArch64 → little-endian
WASM32  → little-endian
```

ABI descriptor vẫn phải ghi explicit endian.

---

# 13. Pointer representation

Native pointer:

```text
Ptr<T>
```

có representation:

```text
machine_word
```

theo target ABI.

---

# 14. Pointer width

Baseline:

```text
x86_64  = 64 bit
AArch64 = 64 bit
WASM32  = 32 bit
```

Không được hard-code `usize == 64` trong compiler frontend.

---

# 15. Pointer alignment

Pointer alignment lấy từ target ABI.

---

# 16. Integer ABI

Canonical scalar types:

```text
i8   i16   i32   i64
u8   u16   u32   u64
isize usize
```

---

# 17. Integer representation

Axiom sử dụng two's complement cho signed integer.

---

# 18. Boolean representation

```text
bool
```

logical values:

```text
false = 0
true  = 1
```

ABI representation phải được xác định theo target, nhưng function boundary không được cho phép giá trị boolean ngoài domain hợp lệ.

---

# 19. Character representation

Axiom `char` không được đồng nhất với C `char`.

Khuyến nghị:

```text
char = Unicode scalar value
```

với ABI representation được target ABI xác định.

Raw byte phải dùng:

```text
u8
```

---

# 20. Floating point

Baseline:

```text
f32
f64
```

IEEE-754 representation được sử dụng khi target hỗ trợ native IEEE semantics.

---

# 21. Floating-point ABI

ABI phải xác định:

- register class;
- stack class;
- alignment;
- return register;
- NaN behavior;
- aggregate interaction.

---

# 22. SIMD/vector types

Axiom hỗ trợ:

```text
vec<T, N>
```

và target-specific native vectors.

---

# 23. Vector ABI

Vector phải có:

```text
size
alignment
register class
pass/return rule
```

---

# 24. Opaque SIMD

Nếu target không có native vector register tương ứng, compiler có thể lower thành aggregate theo ABI.

---

# 25. Machine register classes

ABI descriptor định nghĩa:

```text
INTEGER
FLOAT
VECTOR
SPECIAL
FLAGS
```

---

# 26. Register ownership

Mỗi ABI phải phân loại:

```text
CALLER_SAVED
CALLEE_SAVED
RESERVED
SPECIAL
```

---

# 27. Caller-saved

Caller phải giả định các register caller-saved có thể bị callee phá hủy.

---

# 28. Callee-saved

Callee phải restore trước khi return.

---

# 29. Reserved registers

Một số registers có thể dành cho:

- stack pointer;
- frame pointer;
- TLS;
- platform runtime;
- linker/runtime mechanisms.

Compiler không được allocate chúng tùy tiện.

---

# 30. Frame pointer

Frame pointer không bắt buộc nếu:

```text
debug/unwind/optimization
```

cho phép omit.

---

# 31. Stack pointer

SP phải luôn tuân thủ platform ABI.

Không được sử dụng stack memory trước khi SP hợp lệ.

---

# 32. Stack alignment

Mỗi target ABI định nghĩa:

```text
required_call_alignment
required_entry_alignment
```

---

# 33. Red zone

Nếu platform ABI hỗ trợ red zone:

AXABI ghi explicit.

Không được giả định red zone tồn tại trên mọi target.

---

# 34. Stack growth

Native ABI phải ghi:

```text
grows_down
```

hoặc architecture-specific semantics.

---

# 35. Shadow/home space

Nếu platform ABI yêu cầu caller reserve home/shadow space:

AXABI phải mô tả explicit.

Ví dụ Windows x64.

---

# 36. Parameter classification

Mỗi parameter được classify thành:

```text
INTEGER
FLOAT
VECTOR
AGGREGATE
MEMORY
```

---

# 37. Register parameter passing

Parameter được đưa vào register nếu còn register class capacity.

---

# 38. Stack parameter passing

Nếu register capacity exhausted:

```text
parameter → stack slot
```

---

# 39. Mixed parameters

Integer và floating-point arguments có register banks độc lập nếu target ABI yêu cầu.

---

# 40. Aggregate classification

Struct/union/tuple không được đơn giản mặc định là “memory”.

Compiler phải áp dụng target ABI classification.

---

# 41. Small aggregate

Aggregate nhỏ có thể truyền trong:

- integer registers;
- vector registers;
- multiple registers.

---

# 42. Large aggregate

Aggregate vượt giới hạn ABI được truyền qua memory.

---

# 43. Hidden return pointer

Nếu return value không thể truyền trực tiếp:

```text
caller allocates result
        ↓
hidden result pointer
        ↓
callee writes result
```

---

# 44. Hidden parameters

ABI phải mô tả thứ tự của:

- result pointer;
- generic metadata;
- closure environment;
- user parameters.

Không được để compiler tự suy diễn.

---

# 45. Return values

Return class:

```text
VOID
INTEGER
FLOAT
VECTOR
AGGREGATE_REG
AGGREGATE_MEMORY
```

---

# 46. Multi-register return

Small aggregate có thể trả về nhiều registers nếu target ABI cho phép.

---

# 47. Tuple return

Axiom tuple:

```text
(T1, T2, ...)
```

được ABI-classify như aggregate.

Không có “tuple runtime”.

---

# 48. Struct return

Struct return phải deterministic theo field layout + target ABI.

---

# 49. Union return

Union ABI dựa trên physical size/alignment và target classification.

---

# 50. Enum ABI

Enum representation gồm:

```text
discriminant
```

và payload nếu enum có payload.

---

# 51. Tagged union

Ví dụ:

```text
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

không có ABI đặc biệt riêng.

Nó được lower thành aggregate theo layout ABI.

---

# 52. Niche optimization

Compiler có thể optimize representation:

```text
Option<Ptr<T>>
```

nếu semantics cho phép.

Nhưng ABI-stable public types không được thay đổi representation giữa ABI versions.

---

# 53. ABI-stable types

Để expose binary API, khuyến nghị:

```text
#[abi_stable]
```

cho:

- scalar;
- fixed-layout struct;
- C-compatible enum;
- explicit pointer;
- explicit array/slice ABI.

---

# 54. Non-stable types

Compiler nội bộ có thể tự do optimize:

- generic types;
- closures;
- compiler-generated aggregates;
- inferred layouts.

---

# 55. Struct layout

Axiom struct layout gồm:

```text
field order
field offsets
padding
alignment
size
```

---

# 56. Default struct layout

Struct mặc định được layout deterministic.

Không được randomize field order.

---

# 57. Explicit layout

Cho FFI:

```text
#[repr(C)]
```

hoặc equivalent ABI attribute.

---

# 58. Packed layout

Packed structs phải explicit.

Không được mặc định packed.

---

# 59. Alignment attribute

Cho phép:

```text
#[align(N)]
```

với compiler validation.

---

# 60. Field offset

Compiler phải expose compile-time layout metadata cho ABI inspection.

---

# 61. Zero-sized types

ZST không được tạo ABI ambiguity.

---

# 62. Empty struct

Empty struct có ABI representation target-defined.

Khi crossing FFI boundary phải dùng explicit representation.

---

# 63. Arrays

```text
[T; N]
```

representation:

```text
N contiguous T
```

---

# 64. Slices

Slice không phải C array.

Canonical conceptual representation:

```text
Slice<T> {
    pointer
    length
}
```

---

# 65. Slice ABI

Axiom-to-Axiom ABI có thể truyền slice trực tiếp.

C ABI cần adapter:

```text
pointer + length
```

---

# 66. Strings

Axiom `String` không mặc định tương đương:

```text
char*
```

---

# 67. String FFI

C ABI adapter phải explicit:

```text
pointer
length
encoding contract
ownership contract
```

---

# 68. Ownership ABI

ABI không truyền ownership semantics implicitly.

Một pointer ABI phải có contract:

```text
BORROWED
OWNED
OUT
INOUT
CALLER_FREES
CALLEE_FREES
```

---

# 69. Pointer safety

ABI không tự làm pointer safe.

Safety contract nằm trong type/API metadata.

---

# 70. Function pointer

Function pointer gồm:

```text
code_address
```

theo native ABI.

---

# 71. Function pointer compatibility

Hai function pointer types chỉ tương thích nếu parameter/return ABI tương thích.

---

# 72. Closures

Closure object không được giả định là function pointer.

Canonical conceptual model:

```text
Closure {
    code_pointer
    environment_pointer
}
```

---

# 73. Closure ABI

Internal Axiom ABI có thể sử dụng pair:

```text
(code, env)
```

hoặc compiler-specific fat representation.

---

# 74. Closure FFI

Closure không được tự động convert thành C function pointer.

Phải có explicit trampoline.

---

# 75. Trampoline

```text
C callback
   ↓
Axiom trampoline
   ↓
closure
```

---

# 76. Generic functions

Generic functions không bắt buộc có stable ABI.

Compiler có thể monomorphize.

---

# 77. Generic ABI identity

Mỗi monomorphized instantiation có symbol identity riêng.

---

# 78. Trait dispatch

Static dispatch:

```text
compile-time
```

Dynamic dispatch nếu có:

```text
explicit vtable
```

---

# 79. Vtable ABI

Nếu exported binary ABI sử dụng trait object:

```text
data_ptr
vtable_ptr
```

vtable layout phải versioned.

---

# 80. Override

Struct-method override được lower thành function/vtable/direct call tùy dispatch mode.

ABI phải xác định function signature sau lowering.

---

# 81. Method ABI

Method:

```text
fn draw(self: &Widget)
```

được lower thành conceptual:

```text
draw(self_ptr)
```

Không có hidden class object.

---

# 82. Receiver placement

Receiver được classify như một ABI parameter.

---

# 83. `self` by value

By-value receiver được aggregate-classify như parameter thông thường.

---

# 84. Async functions

Async source function không trực tiếp có ABI của state machine source-level.

Compiler lower thành explicit task/state object.

---

# 85. Async ABI

External ABI phải expose một explicit ABI type.

Ví dụ:

```text
fn foo() -> Task<Result<T>>
```

không được phụ thuộc implementation-specific coroutine layout nếu exported ABI-stable.

---

# 86. Task ABI

AXTASK owns task representation.

AXABI chỉ quy định cách task handle được truyền.

---

# 87. Variadic functions

Axiom variadic functions:

```text
fn log(format: String, args...)
```

không được mặc định tương thích C varargs.

---

# 88. C variadic ABI

C FFI phải có explicit:

```text
extern "c" fn printf(...)
```

và target-specific C varargs lowering.

---

# 89. Variadic register save area

AXABI phải model target-required:

- register save area;
- overflow argument area;
- floating-point argument metadata.

---

# 90. Type promotion

C varargs promotions:

```text
float → double
small integer → int
```

phải được compiler FFI layer áp dụng khi gọi C varargs.

---

# 91. Axiom variadic

Axiom-native variadic calls nên dùng type-safe argument container nếu có thể.

---

# 92. Calling convention names

Baseline:

```text
"axiom"
"c"
"system"
"platform"
```

Target-specific conventions mở rộng:

```text
"win64"
"sysv64"
"aapcs64"
```

---

# 93. Native Axiom convention

`"axiom"` là canonical Axiom ABI.

Nó phải tối ưu cho Axiom compiler/runtime.

---

# 94. Platform ABI

Native `"platform"` maps tới OS toolchain ABI.

---

# 95. Windows x64

Baseline mapping:

```text
axiom
→ Axiom-compatible Windows x64 ABI
```

với interoperability adapter khi C ABI yêu cầu.

---

# 96. Linux x86_64

Baseline:

```text
System V AMD64 ABI
```

cho `extern "c"`.

---

# 97. AArch64

Baseline C ABI:

```text
AAPCS64
```

cho foreign interoperability.

---

# 98. WASM ABI

WASM function signatures sử dụng:

```text
i32
i64
f32
f64
```

và các reference/value types nếu profile cho phép.

---

# 99. WASM aggregate lowering

Struct/tuple phải lower thành scalar parameters/returns hoặc memory representation theo WASM ABI profile.

---

# 100. WASM component boundary

Nếu Component Model được hỗ trợ, ABI riêng phải được version hóa và không được nhầm với raw core WASM ABI.

---

# 101. Name mangling

Axiom internal symbol mangling phải encode tối thiểu:

```text
module
namespace
symbol
generic identity
ABI-relevant type identity
```

---

# 102. Mangling stability

Compiler version không được tùy tiện thay đổi mangled names trong cùng ABI major.

---

# 103. Symbol escaping

Tên source Unicode được encode deterministic thành symbol-safe representation.

---

# 104. C symbols

`extern "c"` không mangling.

Ví dụ:

```text
extern "c" fn ax_init()
```

→ symbol:

```text
ax_init
```

theo platform object ABI.

---

# 105. Export names

Có thể explicit:

```text
#[export("my_function")]
```

để ổn định external symbol.

---

# 106. Import names

Tương tự:

```text
#[import("foo")]
```

---

# 107. Symbol aliases

ABI descriptor cho phép alias symbols.

---

# 108. Versioned symbols

ELF versioned symbols phải được represent trong ABI/link metadata.

---

# 109. TLS ABI

TLS model:

```text
LOCAL_EXEC
INITIAL_EXEC
LOCAL_DYNAMIC
GENERAL_DYNAMIC
PLATFORM_NATIVE
```

tùy target.

---

# 110. TLS variable ABI

```text
thread_local static COUNTER: i64
```

được compiler lower theo target TLS model.

---

# 111. TLS performance

Hot TLS access phải có fast path tương ứng target.

---

# 112. TLS dynamic libraries

Dynamic TLS registration thuộc AXLOADER/platform loader.

---

# 113. TLS initialization

Initialization ordering phải deterministic.

---

# 114. Unwind ABI

AXABI phải định nghĩa contract giữa:

```text
compiler
runtime
OS
debugger
diagnostics
```

---

# 115. Unwind mechanisms

Targets có thể dùng:

```text
DWARF CFI
Windows UNWIND_INFO
Mach-O compact unwind
WASM exception metadata
```

---

# 116. Zero-cost normal execution

Unwind metadata không được yêu cầu overhead trên normal function call ngoài chi phí cần thiết cho ABI.

---

# 117. Panic model

Axiom phải phân biệt:

```text
RETURN_ERROR
PANIC
TRAP
UNWIND
ABORT
```

---

# 118. ABI panic boundary

Không được unwind Axiom exception xuyên qua C ABI boundary trừ khi explicit supported adapter.

---

# 119. C exception boundary

C++ exceptions không được tự động xuyên qua Axiom ABI.

---

# 120. Foreign unwind

Nếu cần interoperable unwind:

```text
extern "platform-unwind"
```

phải explicit.

---

# 121. Setjmp/longjmp

C `setjmp/longjmp` interoperability phải được xem là ABI-sensitive.

Compiler/runtime phải bảo toàn contract của platform.

---

# 122. Stack unwinding metadata

AXCOMPILER emits unwind information.

AXOBJECT transports it.

AXLINKER combines it.

AXBINARY serializes it.

AXLOADER registers/activates platform structures where required.

---

# 123. Debug ABI

Debug metadata phải expose:

```text
function boundaries
parameter locations
register mappings
stack locations
type layouts
source mappings
```

---

# 124. Optimized variables

Debug info không được thay đổi machine ABI chỉ để debug.

---

# 125. Calling convention IR

Compiler IR phải encode explicit:

```text
CallConv
ParamClass
ReturnClass
```

---

# 126. ABI lowering stage

Pipeline:

```text
Typed IR
   ↓
ABI lowering
   ↓
Machine-oriented IR
   ↓
instruction selection
```

---

# 127. ABI lowering must happen before register allocation

Bởi compiler phải biết chính xác:

- registers;
- stack slots;
- hidden arguments;
- return locations.

---

# 128. Call lowering

```text
Source Call
   ↓
Type check
   ↓
ABI classify
   ↓
assign registers
   ↓
assign stack
   ↓
emit call
```

---

# 129. Tail calls

ABI phải định nghĩa khi nào tail call hợp lệ.

---

# 130. Tail-call optimization

Không được thực hiện nếu:

- calling conventions incompatible;
- stack requirements incompatible;
- callee requires hidden state không tương thích.

---

# 131. Sibling calls

Compiler có thể reuse current frame nếu ABI permits.

---

# 132. Stack argument area

ABI lowering tạo explicit:

```text
OutgoingArgArea
```

---

# 133. Stack slot alignment

Mỗi argument stack slot được align theo ABI.

---

# 134. Struct padding

Padding bytes không được coi là initialized semantic data trừ khi explicit.

---

# 135. FFI security

C ABI boundary là unsafe boundary.

Axiom compiler không thể tự chứng minh foreign function contract.

---

# 136. FFI declaration

```text
extern "c" {
    fn malloc(size: usize) -> *mut u8;
}
```

phải đánh dấu unsafe nếu semantics yêu cầu.

---

# 137. ABI attributes

Baseline:

```text
#[abi("axiom")]
#[abi("c")]
#[repr(C)]
#[export("name")]
#[import("name")]
#[cdecl]
```

Tên syntax cuối cùng có thể được compiler spec điều chỉnh nhưng semantics phải giữ.

---

# 138. ABI metadata

Object artifact phải chứa:

```text
ABI fingerprint
calling convention
target
endianness
pointer width
```

---

# 139. ABI mismatch diagnostics

Linker phải báo rõ:

```text
expected ABI X
found ABI Y
```

thay vì generic “symbol incompatible”.

---

# 140. Library compatibility

Dynamic library metadata nên expose:

```text
ABI major
ABI minor
ABI fingerprint
```

---

# 141. ABI major

Breaking ABI change:

```text
major += 1
```

---

# 142. ABI minor

Backward-compatible extension:

```text
minor += 1
```

---

# 143. ABI patch

Implementation/metadata fixes không thay đổi binary contract:

```text
patch += 1
```

---

# 144. ABI compatibility checker

API:

```text
abi_compatible(expected, actual)
```

phải trả về structured result.

---

# 145. Compatibility result

```text
AbiCompatibility {
    level
    differences[]
}
```

---

# 146. ABI diff

Tooling phải có:

```text
abi_diff(old, new)
```

để phát hiện:

- field offset change;
- size change;
- alignment change;
- calling convention change;
- symbol change;
- parameter change;
- return change.

---

# 147. ABI manifest

Library có thể phát hành:

```text
library.axabi
```

chứa public ABI surface.

---

# 148. ABI manifest purpose

Dùng cho:

- package manager;
- compiler;
- IDE;
- AI tooling;
- compatibility checker.

---

# 149. AI-readable ABI

AXABI manifest phải có machine-readable schema.

Ví dụ:

```text
AbiFunction {
    name
    symbol
    parameters[]
    return_type
    calling_convention
    visibility
    ownership
    safety
}
```

---

# 150. ABI and AI metadata

AI tooling có thể query:

```text
abi_query_function()
abi_query_type()
abi_query_layout()
abi_query_symbol()
abi_diff()
```

nhưng metadata không được ảnh hưởng runtime semantics.

---

# 151. ABI reflection

Runtime reflection không bắt buộc.

ABI metadata có thể tồn tại chỉ trong build/debug artifact.

---

# 152. Stable public API

Một library muốn ABI stability phải explicit:

```text
#[abi_stable]
```

hoặc package-level equivalent.

---

# 153. Internal API

Không có stability guarantee.

---

# 154. Generic public API

Generic API nên được source-level/package-level interface, không phải binary ABI, trừ khi explicitly instantiated/exported.

---

# 155. Versioned interfaces

Library có thể export:

```text
foo_v1
foo_v2
```

để giữ compatibility.

---

# 156. Dynamic dispatch ABI

Vtable ABI phải bao gồm:

```text
ABI version
type identity
method slots
drop/destructor contract
```

nếu exported.

---

# 157. Drop ABI

Nếu type có destructor:

ABI phải xác định destructor function signature.

---

# 158. Destruction across FFI

Không được free object ở module A bằng allocator module B nếu allocator ABI không tương thích.

---

# 159. Allocator ABI

Axiom ABI phải có explicit allocator boundary:

```text
ax_alloc
ax_free
ax_realloc
```

khi foreign module cần ownership transfer.

---

# 160. Allocator symmetry

Memory allocated by allocator A phải được release bởi compatible deallocator A.

---

# 161. C allocator interop

Không assume:

```text
Axiom allocator == malloc
```

---

# 162. Static data ABI

Global variables exported phải có:

```text
address
size
alignment
mutability
TLS status
```

---

# 163. Function visibility

```text
PRIVATE
LOCAL
HIDDEN
PROTECTED
PUBLIC
IMPORT
EXPORT
```

mapping target-specific.

---

# 164. Symbol visibility

Visibility belongs to object/link ABI, nhưng AXABI định nghĩa semantic categories.

---

# 165. Weak symbols

Axiom ABI có thể support weak symbol semantics khi target hỗ trợ.

---

# 166. Weak symbol policy

Không dùng weak symbols làm dependency mechanism chính của Axiom.

---

# 167. Inline functions

Inline là compiler optimization, không phải ABI guarantee.

---

# 168. Inline ABI

Nếu exported function được inline vào consumer:

ABI-stable API vẫn phải có callable out-of-line implementation nếu contract yêu cầu.

---

# 169. LTO boundary

LTO có thể bypass conventional call boundary internally.

Nhưng final externally visible symbols vẫn phải tuân AXABI.

---

# 170. PGO

PGO không được thay đổi externally visible ABI.

---

# 171. Sanitizer ABI

Sanitizer instrumentation có thể bổ sung hidden calls/metadata nhưng final ABI phải rõ ràng khi module interoperates với unsanitized code.

---

# 172. Profiling ABI

Profiling metadata không được thay đổi calling convention.

---

# 173. Stack maps

Nếu GC không bắt buộc, stack maps chỉ cần cho:

- diagnostics;
- async;
- safepoints nếu runtime tương lai cần;
- precise profiler.

Không tạo GC requirement.

---

# 174. No hidden GC ABI

AXABI không chứa mandatory GC metadata.

---

# 175. No mandatory borrow-checker ABI

Ownership checking là compiler semantic layer, không phải runtime ABI.

---

# 176. Pointer/reference ABI

References được lower thành machine pointer khi crossing native ABI nếu semantics cho phép.

---

# 177. Reference metadata

Nếu Axiom reference có compile-time semantics nhưng runtime representation là pointer, ABI chỉ truyền physical representation.

---

# 178. Fat references

Nếu type cần:

```text
pointer + metadata
```

ABI phải classify aggregate.

---

# 179. Slice references

Slice thường:

```text
ptr + len
```

---

# 180. Trait objects

Trait object thường:

```text
data + vtable
```

nếu exported.

---

# 181. Dynamic library boundary

Dynamic library public ABI phải không phụ thuộc:

```text
compiler internal AST
HIR
MIR
SSA
```

---

# 182. Object boundary

```text
AXCOMPILER
      ↓
ABI lowering
      ↓
AXOBJECT
```

---

# 183. Linker boundary

AXLINKER đọc ABI metadata để reject incompatible modules.

---

# 184. Loader boundary

AXLOADER dùng ABI metadata để chuẩn bị:

- TLS;
- imports;
- platform runtime contracts.

---

# 185. Startup boundary

AXSTARTUP sử dụng platform ABI để tạo `StartupState`.

---

# 186. Runtime boundary

AXRUNTIME sử dụng AXABI để expose runtime functions.

---

# 187. Runtime internal ABI

Runtime internal functions có thể dùng `"axiom"` convention.

---

# 188. Runtime public ABI

Platform-facing runtime functions có thể use:

```text
"platform"
```

hoặc `"c"` khi interoperability yêu cầu.

---

# 189. Syscall ABI

Syscall ABI không phải Axiom public ABI.

Nó thuộc platform adapter/AXPROCESS/AXSTORAGE/etc.

---

# 190. Kernel boundary

AXABI phải không giả định user-space function ABI giống kernel syscall ABI.

---

# 191. Interrupt ABI

Interrupt/trap entry có ABI riêng của kernel/low-level subsystem.

Không nằm trong normal Axiom function ABI.

---

# 192. Machine-specific ABI

Target backend có:

```text
MachineABI
```

được AXABI profile expose.

---

# 193. ABI query API

```text
abi_current()
abi_for_target(target)
abi_fingerprint()
abi_compare(a, b)
abi_diff(a, b)
abi_function_layout(fn)
abi_type_layout(type)
abi_call_lower(call)
```

---

# 194. Type layout API

```text
abi_sizeof(type)
abi_alignof(type)
abi_field_offset(type, field)
abi_enum_layout(type)
abi_union_layout(type)
```

---

# 195. Calling convention API

```text
abi_classify_parameter(type)
abi_classify_return(type)
abi_assign_registers(signature)
abi_stack_layout(signature)
```

---

# 196. Symbol API

```text
abi_mangle(symbol)
abi_demangle(symbol)
abi_export_name(symbol)
abi_import_name(symbol)
```

---

# 197. FFI API

```text
ffi_validate_signature()
ffi_lower_call()
ffi_lower_return()
ffi_make_trampoline()
ffi_check_abi()
```

---

# 198. ABI descriptor serialization

Canonical format:

```text
AXABI descriptor
```

phải deterministic để hash/fingerprint.

---

# 199. ABI descriptor version

```text
AXABI_ABI_1
```

là stable metadata schema cho ABI description itself.

---

# 200. Native Axiom ABI version

```text
AXIOM_NATIVE_ABI_5
```

là baseline ABI contract của Axiom 5.0.

---

# 201. ABI evolution

Không được thay đổi ABI silently.

Mọi breaking change phải:

```text
new ABI major
new fingerprint
```

---

# 202. ABI freeze policy

Một ABI profile chỉ freeze khi có:

- compiler implementation;
- linker support;
- object metadata;
- runtime support;
- FFI tests;
- binary compatibility tests.

---

# 203. ABI golden tests

Mỗi target phải có golden:

```text
sizeof
alignof
field offsets
parameter locations
return locations
mangled names
TLS layout
unwind metadata
```

---

# 204. Compiler verification

AXCOMPILER phải test:

```text
source signature
        ↓
ABI lowering
        ↓
expected machine contract
```

---

# 205. Cross-compiler verification

Có thể xây một ABI conformance compiler nhỏ để kiểm tra backend.

---

# 206. Link compatibility tests

Test:

```text
Axiom object
+
Axiom object
```

và:

```text
Axiom object
+
C object
```

---

# 207. Dynamic library tests

Test:

```text
Axiom EXE
  ↓
Axiom DLL/SO/dylib
```

và ngược lại.

---

# 208. Callback tests

Test:

```text
C
 ↓ callback
Axiom
```

---

# 209. Aggregate tests

Test tất cả:

```text
small struct
large struct
nested struct
vector struct
packed struct
union
enum
tuple
```

---

# 210. Register pressure tests

Functions với:

```text
1
2
4
8
16
many
```

parameters phải produce expected stack/register transitions.

---

# 211. Mixed-class tests

Ví dụ:

```text
fn f(
    i64,
    f64,
    vec<f32,4>,
    SmallStruct
)
```

phải kiểm tra register classification.

---

# 212. Return tests

Test:

```text
scalar return
small struct return
large struct return
multiple-register return
hidden-return-pointer
```

---

# 213. Variadic tests

Test C ABI varargs riêng từng platform.

---

# 214. TLS tests

Test:

```text
main thread
child thread
shared library TLS
dynamic TLS
```

---

# 215. Unwind tests

Test:

```text
panic
stack unwind
foreign frame
debugger unwind
optimized frame
```

---

# 216. ABI fuzzing

Fuzz type combinations:

```text
nested aggregates
alignment
vectors
zero-sized fields
large arrays
```

để phát hiện compiler/linker ABI disagreement.

---

# 217. Differential ABI testing

So sánh:

```text
AXCOMPILER
vs
reference platform ABI implementation
```

---

# 218. ABI inspection tool

Axiom toolchain nên có:

```text
ax abi inspect binary
ax abi inspect library
ax abi diff old new
ax abi type Type
ax abi function symbol
```

---

# 219. ABI manifest example

Conceptual:

```text
abi {
    target = "x86_64-linux"
    native = "axiom"
    pointer = 64

    function foo {
        params = [i64, f64]
        returns = i32
    }
}
```

---

# 220. ABI documentation generation

Compiler có thể generate:

```text
API
ABI
layout
symbols
ownership
safety
```

documentation trực tiếp từ compiled metadata.

---

# 221. Binary size

ABI metadata không nên bắt buộc nằm trong production executable.

Có thể strip thành:

```text
.axabi
```

sidecar artifact.

---

# 222. Production ABI metadata

Chỉ giữ metadata cần cho:

- loader;
- dynamic linking;
- runtime;
- security.

---

# 223. Debug ABI metadata

Detailed type/layout information có thể nằm trong debug artifact.

---

# 224. Reproducibility

ABI descriptor serialization phải deterministic.

---

# 225. Hash stability

Same ABI descriptor:

```text
same bytes
→ same fingerprint
```

---

# 226. Security

ABI parser phải coi ABI metadata là untrusted input khi đọc external artifacts.

---

# 227. ABI parser limits

Giới hạn:

```text
max types
max fields
max functions
max generic parameters
max metadata size
```

---

# 228. No executable metadata

ABI metadata không được chứa executable code.

---

# 229. ABI and signatures

AXTRUST có thể sign ABI manifest.

AXABI không thực hiện cryptographic verification.

---

# 230. ABI and packages

AXPACKAGE có thể reject package binary incompatible với target ABI.

---

# 231. ABI and build cache

AXBUILD cache key phải bao gồm ABI fingerprint khi ABI ảnh hưởng machine artifact.

---

# 232. ABI and compiler cache

Nếu ABI lowering thay đổi:

```text
ABI fingerprint
```

phải invalidate affected object artifacts.

---

# 233. ABI and LTO

LTO may operate below ABI boundary for same compilation unit/link graph.

External symbols remain ABI stable.

---

# 234. ABI and static libraries

Archive member ABI metadata phải compatible với final target.

---

# 235. ABI and shared libraries

Shared library loader phải verify ABI constraints before activation when metadata is available.

---

# 236. ABI and plugins

Plugin interface nên dùng explicit stable ABI version.

---

# 237. Plugin recommendation

Không dùng arbitrary compiler-internal types làm plugin ABI.

---

# 238. ABI and GUI

GUI event callbacks phải dùng explicit ABI-safe callback representation ở native boundary.

---

# 239. ABI and GPU

GPU kernels có ABI riêng:

```text
GPU kernel ABI
```

không được nhầm với CPU function ABI.

AXCOMPUTE sở hữu GPU-specific kernel ABI.

---

# 240. ABI and IPC

IPC serialization ABI không phải function-call ABI.

AXIPC sở hữu wire representation.

---

# 241. ABI and network

Network protocol không sử dụng native memory layout mặc định.

---

# 242. ABI and serialization

Không serialize arbitrary struct bằng raw memory trừ khi explicit stable-layout contract.

---

# 243. ABI and persistence

Persistent file format phải versioned độc lập với ABI.

---

# 244. ABI and atomics

Atomic types phải có target-specific alignment/size/lock-free metadata.

---

# 245. Atomic ABI

```text
atomic<i32>
```

representation phải tương thích target atomic ABI.

---

# 246. Lock-free metadata

Compiler query:

```text
abi_atomic_is_lock_free(type)
```

---

# 247. Memory ordering

Memory ordering semantics thuộc AXMEMORY/concurrency model.

AXABI chỉ đảm bảo machine-level atomic representation/call contract.

---

# 248. Bitfields

Axiom không nên dùng compiler-dependent implicit bitfield ABI.

Nếu cần:

```text
#[bitfield]
```

phải có explicit layout.

---

# 249. Packed bit representation

Bitfield layout phải được frozen trước khi dùng ở FFI.

---

# 250. Bitfield C interop

C bitfields không nên được map tự động nếu layout platform-specific không được xác nhận.

---

# 251. Flexible arrays

C flexible array members cần explicit FFI representation.

---

# 252. `long`

Axiom không có native semantic dependency vào C `long`.

C ABI mapper quyết định:

```text
C long → Axiom integer type
```

theo platform.

---

# 253. `size_t`

Map:

```text
size_t → usize
```

khi width tương ứng.

---

# 254. `ptrdiff_t`

Map:

```text
ptrdiff_t → isize
```

---

# 255. C `char`

Không map semantic `char` của Axiom trực tiếp.

Dùng explicit `u8`/encoding.

---

# 256. C `_Bool`

Map explicit sang Axiom `bool` với ABI conversion nếu cần.

---

# 257. C structs

`repr(C)` phải follow platform C layout.

---

# 258. C unions

`repr(C)` union phải preserve size/alignment/max-member constraints.

---

# 259. C enums

C enum ABI không được giả định giống Axiom rich enum.

FFI layer phải model underlying integer ABI.

---

# 260. C function pointers

`extern "c" fn(...)` được lower theo C calling convention.

---

# 261. Windows C ABI

AXABI phải hỗ trợ Microsoft x64 ABI specifics.

---

# 262. SysV C ABI

AXABI phải hỗ trợ AMD64 SysV classification.

---

# 263. AAPCS64

AXABI phải support AArch64 Procedure Call Standard.

---

# 264. WASM C ABI

C ABI trên WASM phải thông qua target-specific WASM ABI adapter.

---

# 265. ABI adapter

Compiler có thể generate thunk:

```text
Axiom ABI
   ↓
ABI thunk
   ↓
C ABI
```

---

# 266. Thunk properties

Thunk phải:

- preserve registers;
- adapt parameters;
- adapt return;
- adapt ownership only when explicitly defined;
- adapt calling convention.

---

# 267. No hidden allocation

ABI thunk không tự allocate trừ khi representation conversion bắt buộc.

---

# 268. String thunk

String conversion may allocate; contract phải explicit.

---

# 269. Exception thunk

Không tự propagate exceptions across incompatible boundaries.

---

# 270. Callback thunk

Generated callback trampoline phải có stable lifetime.

---

# 271. Function address stability

Exported function address phải remain valid trong module lifetime.

---

# 272. Hot reload

Hot reload không thuộc AXABI core.

Nếu được hỗ trợ sau này, ABI versioning phải giữ contract.

---

# 273. ABI and JIT

JIT-generated code phải obey same ABI khi gọi native functions.

---

# 274. JIT call bridge

```text
JIT
 ↓
AXABI call lowering
 ↓
native function
```

---

# 275. Foreign assembly

Inline assembly có thể explicitly select calling convention/register contract.

---

# 276. Inline assembly safety

Compiler phải reject clobbers trái với ABI.

---

# 277. Register clobber metadata

Assembly block phải khai báo:

```text
inputs
outputs
clobbers
memory
```

---

# 278. Naked functions

Nếu Axiom hỗ trợ:

```text
@naked
```

compiler không tự emit normal prologue/epilogue.

Người viết chịu trách nhiệm ABI.

---

# 279. Naked function restrictions

Naked function phải explicit unsafe/low-level.

---

# 280. Interrupt functions

```text
@interrupt
```

dùng ABI riêng, không phải normal function ABI.

---

# 281. ABI conformance levels

```text
CORE
FFI
UNWIND
TLS
VECTOR
VARARGS
DEBUG
```

cho phép target support incremental.

---

# 282. Minimal target

WASM minimal target có thể không support:

```text
TLS
native unwind
OS varargs
```

nhưng vẫn có core ABI.

---

# 283. ABI capability descriptor

```text
AbiCapabilities {
    variadic
    unwind
    tls
    vectors
    dynamic_linking
    c_ffi
}
```

---

# 284. Compiler target validation

Trước codegen:

```text
target
 +
ABI
 +
language features
```

phải được validate.

---

# 285. Unsupported ABI feature

Compiler phải fail compile-time thay vì silently fallback sai ABI.

---

# 286. ABI error

```text
ABI_UNSUPPORTED_FEATURE
ABI_MISMATCH
ABI_INVALID_LAYOUT
ABI_REGISTER_EXHAUSTION
ABI_INVALID_SIGNATURE
ABI_FFI_INCOMPATIBLE
```

---

# 287. ABI diagnostic quality

Diagnostic phải chỉ rõ:

```text
function
parameter
expected class
actual class
target
ABI
```

---

# 288. ABI lowering determinism

Cùng:

```text
signature
target
ABI
```

phải tạo cùng ABI assignment.

---

# 289. Parallel compiler

ABI classifier phải thread-safe/pure để compiler có thể chạy parallel.

---

# 290. ABI cache

Target ABI descriptors có thể immutable-cache.

---

# 291. ABI object identity

ABI profile nên được interned/canonicalized trong compiler session.

---

# 292. ABI memory footprint

ABI descriptor phải nhỏ và immutable.

---

# 293. Runtime dependency

AXABI description không yêu cầu runtime.

---

# 294. Compiler dependency

AXABI implementation phải là pure compiler/toolchain component.

---

# 295. Self-hosting requirement

AXCOMPILER viết bằng Axiom phải có thể compile chính ABI lowering code bằng AXABI.

---

# 296. Bootstrap sequence

```text
Stage0 compiler
    ↓
AXABI implementation
    ↓
Stage1 compiler
    ↓
ABI conformance tests
    ↓
Stage2 compiler
```

---

# 297. Bootstrap convergence

Stage1 và Stage2 phải generate ABI-equivalent output cho canonical ABI tests.

---

# 298. ABI golden binary

Mỗi target có canonical binaries:

```text
abi-call-golden
abi-return-golden
abi-aggregate-golden
abi-ffi-golden
```

---

# 299. Formal invariants

```text id="9d9r5f"
ABI-INV-01
Mọi native function call phải tuân một ABI profile xác định.

ABI-INV-02
ABI profile phải identify target architecture.

ABI-INV-03
ABI profile phải identify platform/OS ABI khi cần.

ABI-INV-04
ABI profile phải xác định pointer width.

ABI-INV-05
ABI profile phải xác định endianness.

ABI-INV-06
ABI profile phải xác định scalar representation.

ABI-INV-07
ABI profile phải xác định register classes.

ABI-INV-08
ABI profile phải xác định caller-saved registers.

ABI-INV-09
ABI profile phải xác định callee-saved registers.

ABI-INV-10
ABI profile phải xác định stack alignment.

ABI-INV-11
ABI profile phải xác định parameter classification.

ABI-INV-12
ABI profile phải xác định return classification.

ABI-INV-13
Aggregate passing không được phụ thuộc implementation ngẫu nhiên.

ABI-INV-14
Struct layout phải deterministic.

ABI-INV-15
Struct field offsets phải xác định được tại compile time.

ABI-INV-16
C ABI phải là explicit calling convention.

ABI-INV-17
Axiom ABI không được mặc định tương đương C ABI.

ABI-INV-18
C varargs phải có explicit platform lowering.

ABI-INV-19
Axiom variadic ABI không được tự động coi là C varargs.

ABI-INV-20
Closure ABI không được giả định là raw function pointer.

ABI-INV-21
Trait-object ABI phải explicit nếu crossing binary boundary.

ABI-INV-22
Generic internal ABI không được mặc định là stable public ABI.

ABI-INV-23
Hidden ABI parameters phải được compiler specification xác định.

ABI-INV-24
Hidden return pointers phải có deterministic placement.

ABI-INV-25
Function pointers phải có compatible calling convention.

ABI-INV-26
TLS ABI phải được target profile xác định.

ABI-INV-27
Unwind ABI phải được target profile xác định.

ABI-INV-28
Axiom exceptions/panics không được tự động xuyên C ABI boundary.

ABI-INV-29
Foreign exceptions không được tự động xuyên Axiom ABI boundary.

ABI-INV-30
Allocator ownership crossing module boundary phải explicit.

ABI-INV-31
ABI fingerprint phải deterministic.

ABI-INV-32
ABI breaking change phải tạo ABI major/fingerprint mới.

ABI-INV-33
Object artifacts phải mang đủ ABI identity để linker validate.

ABI-INV-34
Dynamic libraries phải expose ABI compatibility metadata khi yêu cầu stable ABI.

ABI-INV-35
ABI lowering phải hoàn tất trước register allocation.

ABI-INV-36
ABI lowering phải deterministic và thread-safe.

ABI-INV-37
ABI metadata không được chứa executable code.

ABI-INV-38
ABI parser phải xử lý external metadata như untrusted input.

ABI-INV-39
ABI implementation phải có cross-target conformance tests và bootstrap verification.

ABI-INV-40
AXABI chỉ định nghĩa machine/binary contract; semantic type checking và runtime behavior thuộc các subsystem tương ứng.
```

---

# 300. Definition of Done

`AXABI 5.0` được freeze khi hoàn thành:

### Core

- scalar ABI;
- register classes;
- calling convention;
- stack layout;
- parameter passing;
- return passing;
- aggregate classification;
- alignment;
- struct/enum/union layout;
- pointer/function-pointer ABI.

### Advanced

- generic lowering;
- closure ABI;
- trait-object ABI;
- vector ABI;
- variadic ABI;
- TLS ABI;
- unwind ABI;
- panic boundary;
- allocator boundary;
- symbol mangling.

### FFI

- C ABI;
- Windows x64;
- SysV AMD64;
- AAPCS64;
- WASM ABI;
- callbacks;
- trampolines;
- foreign objects.

### Toolchain

- AXCOMPILER lowering;
- AXOBJECT metadata;
- AXLINKER validation;
- AXLOADER integration;
- AXSTARTUP integration;
- AXBUILD cache fingerprint;
- ABI inspection;
- ABI diff.

### Validation

- golden ABI tests;
- aggregate tests;
- register/stack tests;
- FFI tests;
- TLS tests;
- unwind tests;
- fuzzing;
- differential testing;
- bootstrap convergence;
- self-hosted compiler.

**AXABI 5.0 → FROZEN.**

---

# Kiến trúc compiler/toolchain hiện tại

```text
                         SOURCE
                           │
                           ▼
                     ┌───────────┐
                     │ AXCOMPILER│
                     └─────┬─────┘
                           │
                      semantic IR
                           │
                           ▼
                      ABI LOWERING
                           │
                           ▼
                       ┌───────┐
                       │ AXABI │
                       └───┬───┘
                           │
                    machine-oriented IR
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
       AXASSEMBLER                    optimizer
             │                           │
             └─────────────┬─────────────┘
                           ▼
                       AXOBJECT
                           │
                           ▼
                       AXLINKER
                           │
                           ▼
                       AXBINARY
                           │
                           ▼
                       AXLOADER
                           │
                           ▼
                      AXSTARTUP
                           │
                           ▼
                       AXRUNTIME
                           │
                           ▼
                       AXPROCESS
```

Điểm quan trọng của task này là từ đây **machine-level function contract đã có một subsystem độc lập**. Compiler không còn được phép “ngầm quyết định” calling convention trong từng backend; tất cả parameter/return/register/stack/aggregate decisions phải đi qua `AXABI`.

---

# BOOTSTRAP-780 — AXRUNTIME

**Native Axiom Runtime Core, Process Runtime State, Global Initialization, Allocator Integration, Panic/Trap Boundary, Thread Runtime, Task/Async Runtime Bridge, TLS Runtime, I/O/OS Abstraction, Runtime Services Registration, Minimal/Full Runtime Profiles & Application Handoff 5.0**

Đây là bước tiếp theo: sau `AXSTARTUP` và `AXABI`, cần xây **AXRUNTIME** — lớp runtime thực sự nằm giữa startup/process infrastructure và chương trình Axiom. Đây cũng là nơi phải đặc biệt giữ đúng mục tiêu ban đầu của Axiom: **runtime nhỏ, không GC bắt buộc, không hidden allocation, không bắt mọi executable phải kéo theo một “runtime khổng lồ”.**