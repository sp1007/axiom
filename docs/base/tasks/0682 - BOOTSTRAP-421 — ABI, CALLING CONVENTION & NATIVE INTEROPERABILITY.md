# BOOTSTRAP-421 — ABI, CALLING CONVENTION & NATIVE INTEROPERABILITY

**BOOTSTRAP-420 đã khóa.** Ta tiếp tục đúng numbering với **421**, không reset.

Mục tiêu của 421 là biến machine-code/object pipeline thành một compiler có thể **gọi hàm giữa các module, gọi OS/library native, export API và tương tác với C ABI** mà không cần đưa complexity của ABI vào semantic core của Axiom.

---

## 421.1 — ABI architecture

ABI phải được tách thành 3 tầng:

```text
Axiom Language ABI
        │
        ▼
Axiom Target ABI
        │
        ▼
Platform ABI
```

Ví dụ:

```text
Axiom
 ↓
x86-64 ABI layer
 ↓
System V AMD64
```

hoặc:

```text
Axiom
 ↓
x86-64 ABI layer
 ↓
Windows x64
```

hoặc:

```text
Axiom
 ↓
AArch64 ABI layer
 ↓
AAPCS64 / platform ABI
```

Compiler semantic core **không biết** register `RDI`, `RCX`, `X0`...

---

# 421.2 — ABI Descriptor

Mỗi target ABI được mô tả bằng:

```text
ABI {
    architecture
    pointer_size
    stack_alignment

    integer_argument_rules
    float_argument_rules
    vector_argument_rules

    return_rules

    caller_saved_registers
    callee_saved_registers

    parameter_registers
    return_registers

    vararg_rules
    aggregate_rules

    stack_layout_rules
    name_mangling_rules
    tls_rules
    unwind_rules
}
```

Compiler backend sử dụng descriptor này thay vì hard-code ABI rules trong từng pass.

---

# 421.3 — Calling convention

Axiom function declaration có thể có calling convention:

```text
fn foo(a: i32) -> i32
```

mặc định:

```text
callconv = axiom
```

FFI:

```text
extern "c" fn malloc(size: usize) -> *mut u8
```

về mặt compiler:

```text
FunctionType {
    calling_convention = C
}
```

Không nên biến calling convention thành một type riêng biệt trong semantic type system.

Nó là **ABI property của function boundary**.

---

# 421.4 — Calling convention identifiers

Core enum:

```text
AXIOM
C
SYSTEM
FAST
VECTOR
WIN64
SYSV64
AAPCS64
WASM
```

Nhưng implementation không được giả định rằng tất cả tồn tại trên mọi target.

ABI target registry xác định convention nào hợp lệ.

---

# 421.5 — Argument classification

Trước register allocation, compiler tạo:

```text
ABIValue
```

từ:

```text
FunctionParameter
```

Ví dụ:

```text
fn add(a: i32, b: i32)
```

được lower thành:

```text
arg0 → INTEGER
arg1 → INTEGER
```

Sau đó ABI classifier quyết định:

```text
arg0 → register
arg1 → register
```

hoặc stack.

Pipeline:

```text
Axiom Function
      ↓
ABI Classification
      ↓
Machine Arguments
      ↓
Register Allocation
```

---

# 421.6 — Scalar integer arguments

Integer scalar được phân loại theo kích thước/type ABI.

Conceptual classes:

```text
I8
I16
I32
I64
I128
POINTER
```

Không được giả định:

```text
i8 → 8-bit register
```

vì ABI thực tế có thể yêu cầu argument được mở rộng lên register width.

Ví dụ một ABI có thể yêu cầu:

```text
i8 → 64-bit argument register
```

và callee chỉ sử dụng phần thấp cần thiết.

---

# 421.7 — Integer extension

Axiom phải biểu diễn rõ:

```text
sign_extend
zero_extend
truncate
```

tại ABI boundary.

Ví dụ:

```text
fn f(x: i8)
```

ABI lowering có thể tạo:

```text
i8
 ↓
sign/zero extension
 ↓
ABI register representation
```

Không được để machine encoder tự đoán signedness.

---

# 421.8 — Floating-point arguments

Floating types:

```text
f16
f32
f64
f128
```

được ABI classifier phân loại riêng.

Ví dụ:

```text
FLOAT32
FLOAT64
VECTOR
```

ABI quyết định chúng đi:

```text
FP registers
```

hay:

```text
general-purpose registers
```

hay:

```text
stack
```

---

# 421.9 — Vector arguments

Vector type phải có ABI class:

```text
VECTOR128
VECTOR256
VECTOR512
```

nhưng kích thước thực tế phụ thuộc target.

Không được đưa assumption SIMD width vào semantic core.

---

# 421.10 — Aggregate arguments

Đây là phần rất quan trọng.

Struct:

```text
struct Point {
    x: f64
    y: f64
}
```

không đơn giản được coi là một scalar.

ABI classifier có thể quyết định:

```text
Point
 ↓
FP + FP
```

hoặc:

```text
Point
 ↓
INTEGER + INTEGER
```

hoặc:

```text
Point
 ↓
stack
```

Do đó:

```text
AggregateClassification
```

phải là một compiler abstraction.

---

# 421.11 — Struct size và alignment

ABI lowering phải biết:

```text
size
alignment
field offsets
```

nhưng **không được tự tính lại layout struct**.

Layout chính xác phải đến từ:

```text
Axiom Type Layout
```

Sau đó ABI classifier sử dụng kết quả.

Điều này tránh tình trạng:

```text
semantic layout ≠ ABI layout
```

---

# 421.12 — Return value classification

Function result cũng phải qua ABI classifier.

```text
fn f() -> i32
```

→ integer return.

```text
fn f() -> f64
```

→ floating return.

Struct:

```text
fn f() -> Point
```

có thể:

```text
return registers
```

hoặc:

```text
hidden return pointer
```

---

# 421.13 — Hidden parameters

ABI lowering được phép tạo hidden arguments:

```text
fn make_point() -> Point
```

có thể trở thành:

```text
fn make_point(hidden_result_ptr: *Point)
```

Compiler IR phải hỗ trợ:

```text
HiddenABIArgument
```

nhưng source-level function signature không thay đổi.

---

# 421.14 — sret

Đối với ABI sử dụng structure-return pointer:

```text
source:
    fn create() -> LargeStruct
```

lower:

```text
create(result_address)
```

Callee ghi kết quả vào địa chỉ đó.

`result_address` là compiler-generated, không phải source argument.

---

# 421.15 — Caller-saved / callee-saved

ABI descriptor định nghĩa:

```text
caller_saved[]
callee_saved[]
```

Register allocator phải biết chúng.

Call:

```text
foo()
```

có nghĩa:

```text
caller-saved registers
    ↓
may be destroyed

callee-saved registers
    ↓
must survive
```

Compiler không cần tạo save/restore cho register caller-saved trừ khi giá trị live sau call.

---

# 421.16 — Register preservation

Function prologue/epilogue được machine backend tạo từ:

```text
UsedCalleeSavedRegisters
StackFrame
```

Ví dụ:

```text
function
 ↓
save required callee-saved
 ↓
body
 ↓
restore
 ↓
return
```

Không tạo frame cố định nếu function không cần.

---

# 421.17 — Leaf function optimization

Function không call function khác có thể được nhận diện:

```text
LeafFunction
```

Nếu không cần stack frame:

```text
prologue = none
epilogue = none
```

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32 {
    return a + b
}
```

có thể trở thành một sequence machine instruction cực nhỏ.

Đây là một phần quan trọng cho mục tiêu binary nhỏ và hiệu năng cao của Axiom.

---

# 421.18 — Stack frame

Mỗi function có:

```text
StackFrame {
    local_size
    spill_size
    outgoing_arg_size
    alignment
    saved_register_size
}
```

Backend tính:

```text
frame_size
```

sau register allocation.

Không reserve stack trước khi biết spill requirements.

---

# 421.19 — Stack alignment

ABI descriptor quy định:

```text
required_stack_alignment
```

Compiler phải đảm bảo alignment tại mỗi external call boundary.

Không được giả định một giá trị duy nhất cho mọi target.

---

# 421.20 — Red zone

ABI có thể khai báo:

```text
supports_red_zone = true
```

Nếu target cho phép, leaf function có thể sử dụng vùng đó.

Nếu:

```text
freestanding / interrupt / kernel
```

thì target ABI profile có thể disable.

Đây là target policy, không phải language semantic.

---

# 421.21 — Outgoing argument area

Có ABI yêu cầu caller reserve vùng stack cho callee.

ABI descriptor:

```text
outgoing_arg_area_policy
```

điều khiển:

```text
call-site stack allocation
```

Compiler không được hard-code mô hình “push từng argument”.

---

# 421.22 — Variadic functions

Axiom phải hỗ trợ:

```text
extern "c" fn printf(format: *u8, ...)
```

nhưng variadic là **ABI concern**.

Function type:

```text
FunctionType {
    parameters[]
    variadic
}
```

ABI classifier phải biết:

```text
fixed arguments
variadic arguments
```

---

# 421.23 — Variadic state

Một số ABI yêu cầu callee biết:

```text
number of FP register arguments
```

hoặc có register save area.

Do đó function frame có thể chứa:

```text
VarArgSaveArea
```

nếu ABI yêu cầu.

---

# 421.24 — Function pointer

Function pointer:

```text
fn(i32) -> i32
```

được biểu diễn như một ABI-compatible callable pointer.

Call:

```text
f(x)
```

được lower thành:

```text
indirect_call f
```

Không cần object/class dispatch.

---

# 421.25 — Struct-first method model

Thiết kế Axiom trước đây về method không cần class vẫn tương thích ABI.

Ví dụ:

```text
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32
```

Compiler có thể treat:

```text
self
```

như parameter đầu tiên.

Tức là:

```text
v.length()
```

→

```text
length(v)
```

Sau ABI lowering, `v` được classify giống mọi aggregate parameter khác.

Điều này giữ được thiết kế **struct + function**, không cần class ABI đặc biệt.

---

# 421.26 — Method override

Override/dispatch cũng không cần ABI mới.

Một function implementation:

```text
fn draw(self: Shape)
```

vẫn là ordinary function.

Dynamic dispatch nếu được dùng về sau có thể là:

```text
interface/table
    ↓
function pointer
    ↓
ordinary ABI call
```

Như vậy ABI không phụ thuộc vào OOP model.

---

# 421.27 — Closures

Closure:

```text
|x| x + captured
```

không nên được biến thành ABI magic.

Compiler lower thành:

```text
ClosureEnvironment
FunctionPointer
```

Conceptual:

```text
Closure {
    code_ptr
    environment_ptr
}
```

Nhưng representation cuối cùng do closure lowering quyết định.

---

# 421.28 — Closure calling convention

Một closure call có thể lower thành:

```text
fn_ptr(environment_ptr, arguments...)
```

`environment_ptr` là hidden ABI argument.

Điều này cho phép closure sử dụng cùng machine calling infrastructure.

---

# 421.29 — Tail calls

IR phải biểu diễn:

```text
TailCall
```

riêng biệt.

Backend chỉ thực hiện tail-call optimization khi:

```text
ABI-compatible
stack-compatible
calling-convention-compatible
```

Không được biến mọi `return foo()` thành jump một cách mù quáng.

---

# 421.30 — C ABI

Axiom phải có FFI boundary:

```text
extern "c"
```

Ví dụ:

```text
extern "c" {
    fn puts(s: *u8) -> i32
}
```

Compiler cần:

```text
external declaration
 ↓
symbol
 ↓
ABI = C
 ↓
relocation/import
```

---

# 421.31 — Native declaration

External symbol:

```text
extern "c" fn malloc(size: usize) -> *mut u8
```

không chứa implementation.

Compiler tạo:

```text
UndefinedSymbol
```

Linker quyết định symbol được resolve từ:

```text
object
static library
dynamic library
system library
```

---

# 421.32 — Name mangling

Axiom internal symbols có thể sử dụng mangling để tránh collision.

Ví dụ conceptual:

```text
axiom$module$function
```

Nhưng:

```text
extern "c"
```

phải hỗ trợ:

```text
no_mangle
```

để giữ tên ABI chính xác.

---

# 421.33 — Axiom mangling

Mangled name phải encode đủ thông tin cần thiết:

```text
module
namespace
function
generic specialization
ABI-relevant identity
```

Nhưng **không encode implementation details không cần thiết**.

Mục tiêu:

```text
stable enough for linker
```

không phải hứa ABI binary stability vĩnh viễn ngay từ v0.1.

---

# 421.34 — Generic functions

Generic:

```text
fn add<T>(a: T, b: T) -> T
```

sau monomorphization:

```text
add<i32>
add<f64>
```

mỗi specialization trở thành function ABI bình thường.

Ví dụ:

```text
add$i32
add$f64
```

---

# 421.35 — Generic ABI boundary

Axiom không cho phép generic type tự động trở thành C ABI.

Ví dụ:

```text
extern "c" fn foo<T>(...)
```

phải bị reject nếu chưa có ABI representation cụ thể.

FFI phải có type representation xác định.

---

# 421.36 — ABI-safe types

Compiler nên định nghĩa concept:

```text
AbiSafe
```

Các loại primitive thường ABI-safe:

```text
bool
integers
floats
pointers
function pointers
```

Struct chỉ ABI-safe nếu layout đã xác định.

Các abstraction compiler-internal như:

```text
dynamic object
generic type
closure
```

không tự động ABI-safe.

---

# 421.37 — C-compatible structs

Axiom:

```text
@repr(C)
struct Point {
    x: f64
    y: f64
}
```

khóa layout theo C-compatible representation.

Điều này quan trọng cho:

```text
OS APIs
graphics APIs
system libraries
FFI
```

`repr(C)` là ABI/layout attribute, không phải một loại struct khác.

---

# 421.38 — Packed layout

Axiom có thể hỗ trợ:

```text
@repr(packed)
```

nhưng compiler phải cảnh báo/lỗi khi một ABI hoặc target không cho phép thao tác misaligned theo cách yêu cầu.

Không tự động biến mọi struct thành packed.

---

# 421.39 — Alignment-sensitive ABI

ABI classifier phải sử dụng:

```text
TypeLayout {
    size
    alignment
    fields[]
}
```

Do đó:

```text
struct S {
    a: u8
    b: u64
}
```

không được classify trước khi layout hoàn tất.

---

# 421.40 — x86-64 System V

Target profile:

```text
x86_64
ABI = SysV64
```

Phải implement các nhóm chính:

```text
INTEGER
SSE
SSEUP
X87
X87UP
COMPLEX_X87
MEMORY
```

trong aggregate classification.

Integer arguments sử dụng register set theo ABI; floating-point arguments sử dụng register class tương ứng.

Compiler không được hard-code register numbers trong frontend.

---

# 421.41 — Windows x64

Target:

```text
x86_64-windows
ABI = Win64
```

Phải có ABI descriptor riêng.

Đặc biệt:

```text
register argument rules
shadow/home space
stack rules
volatile/nonvolatile registers
return rules
```

không được dùng SysV rules.

Một function compiled cho Windows không được coi là ABI-equivalent với function SysV chỉ vì cả hai đều x86-64.

---

# 421.42 — AArch64

Target:

```text
aarch64
ABI = AAPCS64/platform profile
```

Descriptor phải định nghĩa:

```text
X registers
V registers
stack
aggregate rules
return rules
callee-saved registers
```

Machine encoder chỉ encode instructions.

ABI layer quyết định instruction sequence cần thiết để truyền arguments.

---

# 421.43 — Apple AArch64

Apple target có platform ABI layer riêng trên AArch64.

Architecture:

```text
AArch64
   ↓
AAPCS64-compatible base
   ↓
Apple platform ABI
```

Do đó:

```text
AArch64Encoder
```

không cần biết:

```text
macOS
iOS
```

---

# 421.44 — WASM ABI

WASM không nên ép vào native register ABI.

Target:

```text
WASM32
WASM64
```

có calling convention riêng dựa trên:

```text
WASM value types
linear memory
table/function references
```

Vì vậy:

```text
NativeABI
```

và:

```text
WasmABI
```

là hai implementation của cùng abstraction:

```text
TargetABI
```

---

# 421.45 — TLS

Thread-local:

```text
thread_local var counter: i32
```

không được compiler biến thành một địa chỉ tuyệt đối.

ABI layer cung cấp:

```text
TLSModel
```

ví dụ conceptual:

```text
LOCAL_EXEC
INITIAL_EXEC
LOCAL_DYNAMIC
GENERAL_DYNAMIC
PLATFORM
```

Target quyết định model hợp lệ.

---

# 421.46 — Unwind ABI

Function có thể cần metadata để:

- stack unwinding
- exception handling
- debugger
- profiler

Compiler tạo abstraction:

```text
UnwindInfo
```

Object backend map nó sang:

```text
ELF unwind sections
PE unwind data
Mach-O unwind metadata
```

Unwind generation không được trộn vào machine encoder.

---

# 421.47 — Panic/exception boundary

Axiom core phải phân biệt:

```text
normal return
panic/unwind
abort
```

FFI boundary mặc định:

```text
Axiom ↔ C
```

không được cho phép exception/panic xuyên qua boundary nếu hai ABI không định nghĩa cơ chế tương thích.

Do đó:

```text
Axiom panic
 ↓
FFI boundary
```

phải được xử lý theo explicit policy.

---

# 421.48 — No mandatory runtime ABI

ABI không được phụ thuộc vào Axiom runtime.

Một function:

```text
fn add(a: i32, b: i32) -> i32
```

phải có khả năng compile thành native function độc lập.

Điều này cho phép:

```text
Axiom → Axiom
Axiom → C
C → Axiom
```

mà không bắt buộc link toàn bộ Axiom runtime.

---

# 421.49 — FFI boundary

FFI declaration cần metadata:

```text
ForeignFunction {
    name
    calling_convention
    parameters
    return_type
    linkage
    visibility
}
```

Linkage:

```text
STATIC
DYNAMIC
SYSTEM
WEAK
FRAMEWORK
```

Target có thể mở rộng.

---

# 421.50 — ABI diagnostics

Compiler phải phát hiện:

```text
ABIUnsupportedType
ABIUnsupportedCallingConvention
InvalidVarArg
InvalidFFIType
InvalidReturnType
InvalidAggregateABI
InvalidAlignment
MissingExternalSymbol
ABIAttributeConflict
```

Không được âm thầm thay đổi ABI representation.

---

# 421.51 — ABI conformance tests

Mỗi ABI phải có test matrix:

```text
scalar integer
scalar float
pointer
small struct
large struct
mixed struct
nested struct
array
vector
zero-sized type
return scalar
return struct
many arguments
stack arguments
variadic call
function pointer
external C function
external Axiom function
```

---

# 421.52 — Cross-language ABI tests

Test quan trọng nhất:

```text
C → Axiom
Axiom → C
```

Ví dụ:

```text
C:
    int add(int a, int b);

Axiom:
    extern "c" fn add(a: i32, b: i32) -> i32
```

Hai phía phải nhận cùng:

```text
arguments
return value
stack state
register state
```

---

# 421.53 — ABI golden tests

Compiler phải có expected ABI lowering:

```text
source signature
      ↓
ABI classification
      ↓
expected locations
```

Ví dụ:

```text
arg0 → integer register
arg1 → integer register
arg2 → stack + offset
return → integer register
```

Các golden tests không phụ thuộc binary bytes.

Binary encoder test thuộc **420**.

---

# 421.54 — ABI debugging dump

Compiler option:

```text
--dump-abi
```

có thể xuất:

```text
Function: foo
ABI: SysV64

Arguments:
  a: i32 → GPR0
  b: f64 → FP0
  c: Point → GPR1/GPR2

Return:
  i64 → GPR0

Stack:
  alignment = ...
```

Đây là công cụ cực kỳ hữu ích khi bootstrap compiler.

---

# 421.55 — ABI pipeline hoàn chỉnh

```text
Axiom Type
    ↓
Type Layout
    ↓
Function Signature
    ↓
ABI Classification
    ↓
Argument Assignment
    ↓
Return Assignment
    ↓
Call Lowering
    ↓
Register Allocation
    ↓
Stack Frame
    ↓
Machine Instructions
    ↓
BOOTSTRAP-420 Encoder
```

Điểm quan trọng:

> **420 encode cái ABI lowering đã quyết định; 421 quyết định ABI lowering.**

---

# 421.56 — ABI không làm phình semantic core

Axiom không cần đưa:

```text
register
stack slot
calling convention
callee-saved
relocation
```

vào language syntax thông thường.

Chúng thuộc compiler/backend.

Source-level programmer chỉ cần:

```text
fn foo(...)
extern "c" fn bar(...)
```

và các ABI attributes khi thực sự cần.

---

# 421.57 — Native interoperability model

Axiom chính thức có 4 boundary:

```text
Axiom ↔ Axiom
Axiom ↔ C ABI
Axiom ↔ Platform ABI
Axiom ↔ Raw/System ABI
```

Trong đó:

```text
Axiom ↔ Axiom
```

là default.

```text
Axiom ↔ C
```

là FFI chuẩn.

Platform-specific ABI chỉ dùng khi API yêu cầu.

---

# 421.58 — Raw ABI escape hatch

Đối với low-level programming, Axiom có thể cho phép:

```text
@abi(...)
```

hoặc intrinsic/compiler primitive.

Nhưng đây **không phải API bình thường**.

Mục tiêu là cho phép:

- OS development
- kernel
- bootloader
- embedded
- custom runtime
- SIMD/runtime internals

mà không ép toàn bộ language core phải phức tạp.

---

# 421.59 — ABI stability

Axiom phải phân biệt:

```text
source compatibility
ABI compatibility
object compatibility
```

Compiler version mới có thể thay đổi internal mangling/layout nếu ABI version thay đổi.

External stable ABI chỉ được cam kết khi declaration yêu cầu một ABI cụ thể:

```text
extern "c"
```

---

# 421.60 — ABI versioning

Artifact metadata nên chứa:

```text
Target
Architecture
ABI
ABI version
Object format
Compiler ABI revision
```

Ví dụ:

```text
target = x86_64-linux
abi = sysv64
abi_revision = 1
object = elf64
```

Điều này giúp linker phát hiện object không tương thích thay vì tạo binary sai.

---

# 421.61 — ABI mismatch

Ví dụ:

```text
object A:
    x86_64 + SysV64

object B:
    x86_64 + Win64
```

không được link.

Linker phải báo:

```text
ABI mismatch
```

thay vì giả định chúng tương thích vì cùng ISA.

---

# 421.62 — Final ABI architecture

Toàn bộ backend lúc này trở thành:

```text
                    ┌───────────────┐
                    │ Axiom Types   │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Type Layout   │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ ABI Classifier│
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Call Lowering │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Register Alloc│
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Machine IR    │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Encoder 420   │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Object/Linker │
                    └───────────────┘
```

---

# 421.63 — Completion criterion

**BOOTSTRAP-421 chỉ được DONE khi:**

- Axiom có ABI abstraction.
- Có argument/return classification.
- Có register/stack assignment.
- Có stack-frame rules.
- Có aggregate handling.
- Có variadic model.
- Có function-pointer/call model.
- Có FFI model.
- Có C ABI.
- Có ít nhất SysV64 và Win64 cho x86-64.
- Có AArch64 ABI abstraction.
- Có ABI mismatch detection.
- Có ABI golden tests.
- Có cross-language ABI tests.
- Không đưa ABI complexity vào semantic core.

---

# BOOTSTRAP-422 — MEMORY LAYOUT, DATA REPRESENTATION & TYPE ABI

Task tiếp theo nối trực tiếp với 421.

421 đã trả lời:

> **“Một function truyền dữ liệu qua ABI như thế nào?”**

422 phải trả lời:

> **“Dữ liệu đó thực sự được biểu diễn trong memory như thế nào?”**

Các phần tiếp theo sẽ khóa:

```text
422.1   primitive representation
422.2   integer representation
422.3   float representation
422.4   bool representation
422.5   char / UTF-8
422.6   pointer representation
422.7   slice representation
422.8   string representation
422.9   array layout
422.10  struct layout
422.11  enum layout
422.12  tagged union
422.13  nullable representation
422.14  optional representation
422.15  alignment
422.16  padding
422.17  zero-sized types
422.18  packed representation
422.19  SIMD/vector layout
422.20  atomic representation
422.21  endian
422.22  target data model
422.23  ABI layout compatibility
422.24  @repr(...)
422.25  binary serialization boundary
422.26  FFI representation
422.27  layout guarantees
422.28  compile-time layout introspection
422.29  layout tests
422.30  cross-target conformance
```

**422 sẽ là task tiếp theo trong chuỗi; numbering tiếp tục từ đây.**